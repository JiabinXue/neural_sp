#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""Load dataset for language models (Librispeech corpus).
   You can use the multi-GPU version.
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

from os.path import join
import pandas as pd
import logging
logger = logging.getLogger('training')

from utils.dataset.loader_lm import DatasetBase
from utils.io.labels.word import Idx2word, Word2idx
from utils.io.labels.character import Idx2char, Char2idx


class Dataset(DatasetBase):

    def __init__(self, data_save_path,
                 data_type, data_size, label_type,
                 batch_size, max_epoch=None,
                 max_frame_num=2000, min_frame_num=40,
                 shuffle=False, sort_utt=False, reverse=False,
                 sort_stop_epoch=None, num_gpus=1, tool='htk',
                 num_enque=None, dynamic_batching=False, vocab=False):
        """A class for loading dataset.
        Args:
            data_save_path (string): path to saved data
            data_type (string): train or dev_clean or dev_other or test_clean
                or test_other
            data_size (string): 100 or 460 or 960
            label_type (string): word or characater or characater_capital_divide
            batch_size (int): the size of mini-batch
            max_epoch (int): the max epoch. None means infinite loop.
            max_frame_num (int): Exclude utteraces longer than this value
            min_frame_num (int): Exclude utteraces shorter than this value
            shuffle (bool): if True, shuffle utterances.
                This is disabled when sort_utt is True.
            sort_utt (bool): if True, sort all utterances in the ascending order
            reverse (bool): if True, sort utteraces in the descending order
            sort_stop_epoch (int): After sort_stop_epoch, training will revert
                back to a random order
            num_gpus, int): the number of GPUs
            tool (string): htk or librosa or python_speech_features
            num_enque (int): the number of elements to enqueue
            dynamic_batching (bool): if True, batch size will be chainged
                dynamically in training
            vocab (bool or string):
        """
        self.data_type = data_type
        self.data_size = data_size
        self.label_type = label_type
        self.batch_size = batch_size * num_gpus
        self.max_epoch = max_epoch
        self.shuffle = shuffle
        self.sort_utt = sort_utt
        self.sort_stop_epoch = sort_stop_epoch
        self.num_gpus = num_gpus
        self.tool = tool
        self.num_enque = num_enque
        self.dynamic_batching = dynamic_batching
        self.is_test = True if 'test' in data_type else False

        if vocab and data_size != vocab and not self.is_test:
            self.vocab_file_path = join(
                data_save_path, 'vocab', vocab, label_type + '.txt')
            vocab_file_path_org = join(
                data_save_path, 'vocab', data_size, label_type + '.txt')
        else:
            self.vocab_file_path = join(
                data_save_path, 'vocab', data_size, label_type + '.txt')
        if label_type == 'word':
            self.idx2word = Idx2word(self.vocab_file_path)
            self.word2idx = Word2idx(self.vocab_file_path)
        else:
            self.idx2char = Idx2char(
                self.vocab_file_path,
                capital_divide=label_type == 'character_capital_divide')
            self.char2idx = Char2idx(
                self.vocab_file_path,
                capital_divide=label_type == 'character_capital_divide')

        super(Dataset, self).__init__(vocab_file_path=self.vocab_file_path)

        # Load dataset file
        if data_type == 'train':
            dataset_path = join(
                data_save_path, 'dataset', tool, data_size, 'train_' + data_size, label_type + '.csv')
        else:
            dataset_path = join(
                data_save_path, 'dataset', tool, data_size, data_type, label_type + '.csv')
        df = pd.read_csv(dataset_path, encoding='utf-8')
        df = df.loc[:, ['frame_num', 'input_path', 'transcript']]

        # Remove inappropriate utteraces
        if not self.is_test:
            logger.info('Original utterance num: %d' % len(df))
            df = df[df.apply(
                lambda x: min_frame_num <= x['frame_num'] < max_frame_num, axis=1)]
            logger.info('Restricted utterance num: %d' % len(df))

        # Sort paths to input & label
        if sort_utt:
            df = df.sort_values(by='frame_num', ascending=not reverse)
        else:
            df = df.sort_values(by='input_path', ascending=True)

        self.df = df
        self.rest = set(list(df.index))

    def select_batch_size(self, batch_size, min_frame_num_batch):
        return batch_size