set softtabstop=4 shiftwidth=4
set textwidth=80
set number relativenumber
set nocompatible
set hidden
filetype plugin indent on
syntax on

let s:root = expand('<sfile>:p:h')
execute 'set runtimepath^=' . fnameescape(s:root . '/.vim-local/vim-lsp')

function! s:on_lsp_buffer_enabled() abort
        setlocal omnifunc=lsp#complete
        nmap <buffer> gd <plug>(lsp-definition)
        nmap <buffer> gs <plug>(lsp-document-symbol-search)
        nmap <buffer> gS <plug>(lsp-workspace-symbol-search)
        nmap <buffer> gr <plug>(lsp-references)
        nmap <buffer> K <plug>(lsp-hover)
endfunction

augroup lsp_python
  autocmd!
  autocmd User lsp_setup call lsp#register_server({
                          \ 'name': 'pylsp',
                          \ 'cmd': {server_info -> ['pylsp'] },
                          \ 'allowlist': ['python']
                          \})
  autocmd User lsp_buffer_enabled call s:on_lsp_buffer_enabled()
augroup END

augroup markdown_setting
    autocmd!
    autocmd FileType markdown setlocal wrap linebreak breakindent autoindent
    autocmd FileType markdown setlocal softtabstop=2 shiftwidth=2 
augroup END

