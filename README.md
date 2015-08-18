# clamav

Forked version of clamav with ClearOS changes applied

* git clone git+ssh://git@github.com/clearos/clamav.git
* cd clamav
* git checkout epel7
* git remote add upstream git://pkgs.fedoraproject.org/clamav.git
* git pull upstream epel7
* git checkout clear7
* git merge --no-commit epel7
* git commit
