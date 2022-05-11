#! /bin/bash

# install git or hg version that is used during the test.
set -ev
pwd
if [ "$VCS" = "git" ]; then
  git_dir="$HOME"/git/"$VERSION"
  if [ ! -e "$git_dir"/git ]; then
    mkdir -p "$git_dir"
    git clone https://github.com/git/git.git
    cd git
    git checkout "v$VERSION"
    make configure
    ./configure
    make NO_OPENSSL=YesPlease
    cp bin-wrappers/git "$git_dir"
    cd ..
  fi
  executable="$git_dir"/git
elif [ "$VCS" = "hg" ]; then
  hg_dir="$HOME"/hg/"$VERSION"
  if [ ! -e "$hg_dir"/hg ]; then
    mkdir -p "$hg_dir"
    hg clone https://www.mercurial-scm.org/repo/hg
    cd hg
    hg checkout "$VERSION"
    make local
    cp hg "$hg_dir"
    cd ..
  fi
  executable="$hg_dir"/hg
fi
echo "$VCS"_executable = "$(realpath "$executable")" >> pytest.ini
