# Latin Speech Rate

This is the source code used in ["How fast did Cicero speak? The speech rate of Classical Latin versus its Romance descendants" by Daniel M. Stelzer](https://revistes.uab.cat/isogloss/article/view/v8-n4-stelzer).

Usage notes:
 - This relies on a specially-modified version of CLTK, provided at [dstelzer/cltk](https://github.com/dstelzer/cltk).
 - It also relies on Johan Winge's Latin macronizer, [Alatius/latin-macronizer](https://github.com/Alatius/latin-macronizer). This should be installed at `data/latin/latin-macronizer`.
 - Apart from that, all required libraries should be available on PyPI. This code has been tested on Python 3.8.10 but should be compatible with later versions as well.

You will also need a copy of the PHI corpus, which I don't think I can legally distribute.

The Jupyter notebook "everything.ipynb" will run through all the steps of the experiment, from gathering the data to producing the plots.
