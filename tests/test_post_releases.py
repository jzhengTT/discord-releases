import unittest

import feedparser

from post_releases import is_official

FEED = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>test</title>
  <entry>
    <id>https://github.com/tenstorrent/ttsim/releases/tag/v1.12.1</id>
    <title>ttsim v1.12.1</title>
    <category term="official"/>
    <category term="release"/>
  </entry>
  <entry>
    <id>https://github.com/hedgehope/wolfpine/releases/tag/v2.2</id>
    <title>tt-sim v2.2</title>
    <category term="community"/>
    <category term="release"/>
  </entry>
  <entry>
    <id>https://github.com/moritztng/tt-bio/releases/tag/v0.20.0</id>
    <title>tt-bio v0.20.0</title>
    <category term="affiliated"/>
    <category term="release"/>
  </entry>
  <entry>
    <id>https://example.com/untagged</id>
    <title>untagged</title>
  </entry>
</feed>
"""


class IsOfficialTest(unittest.TestCase):
    def setUp(self):
        self.entries = {e.id: e for e in feedparser.parse(FEED).entries}

    def test_official_entry_is_kept(self):
        self.assertTrue(
            is_official(self.entries["https://github.com/tenstorrent/ttsim/releases/tag/v1.12.1"])
        )

    def test_community_entry_is_dropped(self):
        self.assertFalse(
            is_official(self.entries["https://github.com/hedgehope/wolfpine/releases/tag/v2.2"])
        )

    def test_affiliated_entry_is_dropped(self):
        self.assertFalse(
            is_official(self.entries["https://github.com/moritztng/tt-bio/releases/tag/v0.20.0"])
        )

    def test_untagged_entry_is_dropped(self):
        self.assertFalse(is_official(self.entries["https://example.com/untagged"]))


if __name__ == "__main__":
    unittest.main()
