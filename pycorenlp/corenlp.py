#!/usr/bin/env python
#
# corenlp  - Python interface to Stanford Core NLP tools
# Copyright (c) 2012 Dustin Smith
#   https://github.com/dasmith/stanford-corenlp-python
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import json
import os
import re
import sys
import traceback
import pexpect
from unidecode import unidecode
import glob
from bs4 import BeautifulSoup

use_winpexpect = True

try:
    import winpexpect
except ImportError:
    use_winpexpect = False

VERBOSE = False
DIRECTORY = "stanford-corenlp-full-2015-04-20"


class StanfordCoreNLP:

    """
    Command-line interaction with Stanford's CoreNLP java utilities.
    Can be run as a JSON-RPC server or imported as a module.
    """

    def _xml_2_json(self, xml):
        soup = BeautifulSoup(xml, "xml")

        return {"sentences": [{
            "id": sentence["id"],

            "tokens": [{
                "id": token["id"],
                "word": token.word.text,
                "lemma": token.lemma.text,
                "characterOffsetBegin": token.CharacterOffsetBegin.text,
                "characterOffsetEnd": token.CharacterOffsetEnd.text,
                "pos": token.POS.text,
                "ner": token.NER.text
            } for token in sentence.find_all("token")],

            "parse": sentence.find_all("parse")[0].text,

            "dependencies": [{
                "type": dependency["type"],
                "dependencies": [{
                    "type": sub_dep["type"],
                    "governor": {
                        "idx": sub_dep.governor["idx"],
                        "value": sub_dep.governor.text
                    },
                    "dependent": {
                        "idx": sub_dep.dependent["idx"],
                        "value": sub_dep.dependent.text
                    }
                } for sub_dep in dependency.find_all("dep")]
            } for dependency in sentence.find_all("dependencies")],

            "machineReading": {"entities": [{
                "id": entity["id"],
                "val": entity.text.strip(),
                "start": entity.span["start"],
                "end": entity.span["end"]
            } for entity in sentence.find_all("entity")]}

        } for sentence in soup.root.document.sentences.find_all("sentence")]}


    def _init_corenlp_command(self, corenlp_path, memory, properties):
        """
        Checks the location of the jar files.
        Spawns the server as a process.
        """

        jars = glob.glob(os.path.join(corenlp_path, "*.jar"))
        java_path = "java"
        classname = "edu.stanford.nlp.pipeline.StanfordCoreNLP"

        # include the properties file, so you can change defaults
        # but any changes in output format will break parse_parser_results()
        current_dir_pr =  os.path.join(os.path.dirname(os.path.abspath(__file__)), properties)
        if os.path.exists(properties):
            props = "-props %s" % (properties.replace(" ", "\\ "))
        elif os.path.exists(current_dir_pr):
            props = "-props %s" % (current_dir_pr.replace(" ", "\\ "))
        else:
            raise Exception("Error! Cannot locate: %s" % properties)

        # add memory limit on JVM
        if memory:
            limit = "-Xmx%s" % memory
        else:
            limit = ""

        return "%s %s -cp %s %s %s" % (java_path, limit, ':'.join(jars), classname, props)

    def _spawn_corenlp(self):
        if VERBOSE:
            print self.start_corenlp
        if use_winpexpect:
            self.corenlp = winpexpect.winspawn(self.start_corenlp, maxread=8192,
                searchwindowsize=80)
        else:
            self.corenlp = pexpect.spawn(self.start_corenlp, maxread=8192,
                searchwindowsize=80)

        # show progress bar while loading the models
        if VERBOSE:
            widgets = ['Loading Models: ', Fraction()]
            # Model timeouts:
            # pos tagger model (~5sec)
            # NER-all classifier (~33sec)
            # NER-muc classifier (~60sec)
            # CoNLL classifier (~50sec)
            # PCFG (~3sec)
            timeouts = [20, 200, 600, 600, 20]
            for i in xrange(5):
                self.corenlp.expect("done.", timeout=timeouts[i])  # Load model
                pbar.update(i + 1)
            self.corenlp.expect("Entering interactive shell.")
            pbar.finish()

        # interactive shell
        self.corenlp.expect("\nNLP> ")

    def __init__(self, corenlp_path=DIRECTORY, memory="3g", properties='default.properties'):
        """
        Checks the location of the jar files.
        Spawns the server as a process.
        """

        # spawn the server
        self.start_corenlp = self._init_corenlp_command(corenlp_path, memory, properties)
        self._spawn_corenlp()

    def _close(self, force=True):
        global use_winpexpect
        if use_winpexpect:
            self.corenlp.terminate()
        else:
            self.corenlp.terminate(force)

        if self.corenlp.isalive():
            self._close()


    def _parse(self, text):
        """
        This is the core interaction with the parser.

        It returns a Python data-structure, while the parse()
        function returns a JSON object
        """
        # clean up anything leftover
        def clean_up():
            while True:
                try:
                    self.corenlp.read_nonblocking(8192, 0.1)
                except pexpect.TIMEOUT:
                    break

        # CoreNLP interactive shell cannot recognize newline
        if '\n' in text or '\r' in text:
            to_send = re.sub("[\r\n]", " ", text).strip()
        else:
            to_send = text

        clean_up()

        self.corenlp.sendline(to_send)

        # How much time should we give the parser to parse it?
        # the idea here is that you increase the timeout as a
        # function of the text's length.
        # max_expected_time = max(5.0, 3 + len(to_send) / 5.0)
        max_expected_time = max(300.0, len(to_send) / 3.0)

        # repeated_input = self.corenlp.except("\n")  # confirm it
        t = self.corenlp.expect(["\nNLP> ", pexpect.TIMEOUT, pexpect.EOF,
                                 "\nWARNING: Parsing of sentence failed, possibly because of out of memory."],
                                timeout=max_expected_time)
        incoming = self.corenlp.before
        if t == 1:
            # TIMEOUT, clean up anything left in buffer
            clean_up()
            print >>sys.stderr, {"error": "timed out after %f seconds" % max_expected_time,
                                 "input": to_send,
                                 "output": incoming}
            raise TimeoutError(repr("Timed out after %d seconds" % max_expected_time))
        elif t == 2:
            # EOF, probably crash CoreNLP process
            print >>sys.stderr, {"error": "CoreNLP terminates abnormally while parsing",
                                 "input": to_send,
                                 "output": incoming}
            raise ChildProcessError(repr("CoreNLP process terminates abnormally while parsing"))
        elif t == 3:
            # Out of memory
            print >>sys.stderr, {"error": "WARNING: Parsing of sentence failed, possibly because of out of memory.",
                                 "input": to_send,
                                 "output": incoming}
            raise MemoryError("CoreNLP process terminated while processing because it ran out of memory")

        if VERBOSE:
            print "%s\n%s" % ("=" * 40, incoming)

        try:
            out = re.sub('\s+', ' ', incoming).strip().split('<?xml version="1.0"')[1]
        except Exception as e:
            if VERBOSE:
                print traceback.format_exc()
            raise e

        return '<?xml version="1.0"' + out


    def raw_parse(self, text):
        """
        This function takes a text string, sends it to the Stanford parser,
        and returns the raw XML output from the parser.
        """
        try:
            xml = self._parse(text)
            return xml
        except Exception as e:
            self.corenlp._close()
            self._spawn_corenlp()
            raise e


    def parse(self, text):
        """
        This function takes a text string, sends it to the Stanford parser,
        reads in the result, parses the results and a Python object representation
        of the XML output.
        """
        return self._xml_2_json(self.raw_parse(text))
