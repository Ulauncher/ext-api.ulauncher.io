#!/bin/bash

# To encrypt .aws:
# $ cd ext-api
# $ travis login
# $ export K=...
# $ export IV=...
# $ travis encrypt-file build-utils/aur_key build-utils/aur_key.enc --add -K $K --iv $IV
#
# Note:
# travis cli generates random encryption keys and uploads them to the server
# each time `travis encrypt-file` is run making impossible to encrypt multiple files
# Therefore K and IV keys should be generated beforehand and provided to encrypt-file command
# using -K and --iv args
#
# Commands to generate keys:
# K=$(ruby -rsecurerandom -e 'puts SecureRandom.hex(32).chomp')
# IV=$(ruby -rsecurerandom -e 'puts SecureRandom.hex(16).chomp')


docker run -it --rm \
    -v $(pwd):/home/travis/ext-api \
    -v $HOME/.bash_history:/root/.bash_history \
    mgruener/travis-cli
