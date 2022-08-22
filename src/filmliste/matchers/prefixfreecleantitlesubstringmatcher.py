from filmliste.matchers.matcher import Matcher


class PrefixFreeCleanTitleSubstringMatcher(Matcher):

    def __init__(self, *args, **kwargs) -> None:
        super(self.__class__, self).__init__(*args, **kwargs)

    def where_clause(self) -> str:
        return 'instr(title, :prefix_free_clean_title) > 0'

    def parameters(self) -> dict:
        parameters = super().parameters()

        # The prefix could be a “Spezial: ” prefix that we want to get rid of.
        parameters['prefix_free_clean_title'] = \
            self.clean_title.split(':').pop().strip()

        return parameters
