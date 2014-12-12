Installation
============

Installation from git into virtualenv
-------------------------------------

If you want to play with the most recent development version of manual
labour, the easiest way to do this is to use a developer install into a
virtualenv. For more information about git see http://git-scm.org and about
virtualenv see http://virtualenv.readthedocs.org/en/latest/.

First you need to clone the repository::

  git clone https://github.com/jreinhardt/manual-labour.git <ml-target-directory>

Then you create a virutalenv. You can keep it in the same or in a separate
directory, but a separate one is cleaner::

  virtualenv <ve-target-directory>

Then you need to activate the virtualenv and start a developer install of
manuallabour::

  cd <ml-target-directory>
  . <ve-target-directory>/bin/activate

  python setup.py develop

To make sure that everything worked you can open a interactive python session and type::

  import manuallabour

If there is no :class:`ImportError`, then everything succeeded.

You can only use manuallabour from the terminal where you activated the
virtualenv. If you have closed this terminal, you need to activate it again,
but it is not necessary to run `setup.py` again.

Installation with pip
---------------------





.. todo:: document extras_require:
 # You can install these using the following syntax, for example:
 # $ pip install -e .[dev,test]
 #ubuntu: need to have installed graphviz and graphviz-dev for graph extra

