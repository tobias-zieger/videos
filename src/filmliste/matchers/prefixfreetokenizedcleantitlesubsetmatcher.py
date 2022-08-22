import re
from typing import Set
from filmliste.matchers.matcher import Matcher


def tokenize(string: str) -> Set[str]:
    return set(re.compile('[^a-z ]').sub(string=string.lower(), repl=' ').split(' '))


class PrefixFreeTokenizedCleanTitleSubsetMatcher(Matcher):

    # The tokens from the prefix-free cleaned title must appear in the tokens from the entry's title.

    def __init__(self, *args, **kwargs) -> None:
        super(self.__class__, self).__init__(*args, **kwargs)
        self.prefix_free_clean_title = self.clean_title.split(
            ':').pop().strip()
        self.tokenized_prefix_free_clean_title = tokenize(
            self.prefix_free_clean_title)

    def where_clause(self) -> str:
        return 'instr(title, :prefix_free_clean_title) > 0'

    def parameters(self) -> dict:
        parameters = super().parameters()

        # The prefix could be a “Spezial: ” prefix that we want to get rid of.
        parameters['prefix_free_clean_title'] = \
            self.clean_title.split(':').pop().strip()

        return parameters

    def additional_filter(self, rows: list) -> list:
        result = []
        for row in rows:
            tokenized_title_from_database = tokenize(row['title'])
            if self.tokenized_prefix_free_clean_title.issubset(tokenized_title_from_database):
                result.append(row)

        return result
