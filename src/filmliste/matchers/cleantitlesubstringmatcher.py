from filmliste.matchers.matcher import Matcher


class CleanTitleSubstringMatcher(Matcher):

    def __init__(self, *args, **kwargs) -> None:
        super(self.__class__, self).__init__(*args, **kwargs)

    def where_clause(self) -> str:
        return 'instr(title, :clean_title) > 0'
