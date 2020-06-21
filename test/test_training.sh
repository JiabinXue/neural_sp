#!/usr/bin/env bash

cd ./examples/ci_test || exit 1;

# LM
./run.sh --stop_stage 3 --lm_conf conf/lm/rnnlm.yaml || exit 1;
./run.sh --stop_stage 3 --lm_conf conf/lm/transformerlm.yaml || exit 1;
./run.sh --stop_stage 3 --lm_conf conf/lm/transformer_xl.yaml || exit 1;

# ASR
./run.sh --stage 4 --conf conf/asr/blstm_las.yaml || exit 1;
./run.sh --stage 4 --conf conf/asr/blstm_las.yaml --conf2 conf/data/spec_augment.yaml || exit 1;
./run.sh --stage 4 --conf conf/asr/blstm_las.yaml --conf2 conf/data/adaptive_spec_augment.yaml || exit 1;
./run.sh --stage 4 --conf conf/asr/blstm_transducer.yaml || exit 1;
./run.sh --stage 4 --conf conf/asr/transformer.yaml || exit 1;
./run.sh --stage 4 --conf conf/asr/conformer.yaml || exit 1;
