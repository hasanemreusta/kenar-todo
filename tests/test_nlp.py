import unittest

from todo.nlp import parse_natural

TODAY = "2026-10-21"   # a Wednesday


def p(text):
    return parse_natural(text, TODAY)


class NaturalLanguageTests(unittest.TestCase):
    def test_plain(self):
        r = p("Süt al")
        self.assertEqual((r["title"], r["due"], r["repeat"], r["priority"], r["found"]),
                         ("Süt al", None, "", "medium", []))

    def test_relative_words(self):
        self.assertEqual(p("market yarın")["due"], "2026-10-22")
        self.assertEqual(p("market yarin")["title"], "market")
        self.assertEqual(p("rapor bugün")["due"], TODAY)
        self.assertEqual(p("rapor öbür gün")["due"], "2026-10-23")
        self.assertEqual(p("rapor haftaya")["due"], "2026-10-28")

    def test_weekday_priority_tag(self):
        r = p("rapor cuma !yüksek #iş")
        self.assertEqual((r["title"], r["due"], r["priority"], r["tags"]), ("rapor", "2026-10-23", "high", ["iş"]))
        self.assertEqual([k for k, _ in r["found"]], ["due", "priority", "tag"])

    def test_day_month_and_numeric(self):
        self.assertEqual(p("doktor 25 ekim")["due"], "2026-10-25")
        self.assertEqual(p("doktor 25 ekim")["title"], "doktor")
        self.assertEqual(p("fatura 5.11")["due"], "2026-11-05")
        self.assertEqual(p("fatura 3/1")["due"], "2027-01-03")
        self.assertEqual(p("fatura 3.1.2028")["due"], "2028-01-03")
        self.assertEqual(p("3 elma al")["title"], "3 elma al")      # a number without a month stays in the title

    def test_recurring(self):
        r = p("spor her gün")
        self.assertEqual((r["title"], r["repeat"], r["due"]), ("spor", "daily", TODAY))
        r = p("toplantı her pazartesi")
        self.assertEqual((r["repeat"], r["due"]), ("weekly", "2026-10-26"))
        self.assertEqual(p("kira her ay 1.11")["repeat"], "monthly")
        self.assertEqual(p("kira her ay 1.11")["due"], "2026-11-01")

    def test_weekday_as_first_word_stays_title(self):
        r = p("pazar alışverişi")
        self.assertEqual((r["title"], r["due"]), ("pazar alışverişi", None))

    def test_legacy_tokens_still_work(self):
        r = p("süt @yarın !h")
        self.assertEqual((r["due"], r["priority"]), ("2026-10-22", "high"))
        self.assertEqual(p("x @2026-12-01")["due"], "2026-12-01")

    def test_preview_labels(self):
        labels = [label for _, label in p("rapor yarın her hafta")["found"]]
        self.assertEqual(labels, ["Yarın · 22 Eki", "Her hafta"])


if __name__ == "__main__":
    unittest.main()
