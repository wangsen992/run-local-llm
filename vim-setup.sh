#!/bin/bash


VIM_CONFIG_DIR='.vim-local'

if [[ ! -d ${VIM_CONFIG_DIR} ]]; then
    mkdir ${VIM_CONFIG_DIR}
fi

git clone https://github.com/prabirshrestha/vim-lsp.git \
    ${VIM_CONFIG_DIR}/vim-lsp

    
