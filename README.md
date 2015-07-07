# py-stanford-corenlp

This is a fork of the [Wordseer-specific fork](https://github.com/Wordseer/stanford-corenlp-python) of Dustin Smith's [stanford-corenlp-python](https://github.com/dasmith/stanford-corenlp-python), a Python interface to [Stanford CoreNLP](http://nlp.stanford.edu/software/corenlp.shtml). In contrast to the above-mentioned versions, this version _only_ functions as a Python package, and not as a JSON-RPC server.

## Differences
For a comparison between the Wordseer fork and Dustin Smith's version, please see [the README ](https://github.com/Wordseer/stanford-corenlp-python#edited) of the Wordseer fork. Below is an outline of differences between this version and the Wordseer fork:

+ Removed JSON-RPC server
+ Removed input parameters
+ Removed ````batch_parse````
+ Cleaned up dependencies and unused code
+ Completely reworked Python dictionary/JSON formatting to be based on the standard XML output instead of the serial output. The serial output excludes different fields returned by different annotators, and the structure of the JSON output of the previous version was inconsistent with the XML output, making parsing difficult.
+ Thorough documentation



## Setup

To use this package you must [download](http://nlp.stanford.edu/software/corenlp.shtml#Download) and unpack the zip file containing Stanford's CoreNLP package.  By default, ````corenlp.py```` looks for the Stanford Core NLP folder as a subdirectory of where the script is being run.

Next, clone this repository and run the setup script:

    git clone https://github.com/UW-Macrostrat/py-stanford-corenlp.git
    cd py-stanford-corenlp
    python setup.py install


## Usage

First, import the package and create a parser. The method takes the following parameters:
+ A path to the Stanford CoreNLP package - default is as a subdirectory of where the script is being run.
+ A memory limit - default is 3GB (specified as ````3g````)
+ A properties file - default is ````corenlp/default.properties````


````
from pycorenlp import *

parser = StanfordCoreNLP("/your/path/to/stanford-corenlp-full", "4g", "pycorenlp/default.properties")

....
````

You can then parse text using ````parse```` which returns JSON, or ````raw_parse```` which returns XML.

````
...

output = parser.parse("The quick brown fox jumps over the lazy dog")
print output
````

## License
[GNU GPLv2](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)


## Original developers
   * Hiroyoshi Komatsu [hiroyoshi.komat@gmail.com]
   * Johannes Castner [jac2130@columbia.edu]
   * Robert Elwell [robert@wikia-inc.com]
   * Tristan Chong [tristan@wikia-inc.com]
   * Aditi Muralidharan [aditi.shrikumar@gmail.com]
   * Ian MacFarland [ianmacfarland@ischool.berkeley.edu]
