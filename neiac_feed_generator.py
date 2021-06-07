from requests import get as http_get
from re import compile as regex

item_pattern = regex(r'<item>([\s\S]+?)</item>')
property_pattern = regex(r'<([\w:]+?)(\s.+?)?>([\s\S]+?)</\1>')
enclosure_pattern = regex(r'<enclosure .+?/>')
chapter_pattern = regex(r'[Cc]h (\d+)[-–](\d+)')
desc_chapter_pattern = regex(r'[Cc]hapter(s?) \d+\s?[-–]\s?\d+:[^\.]+')
desc_pattern = regex(r'^[Cc]hapter(s?) \d+\s?[-–]\s?\d+: ')

hpmor_feed = http_get('https://hpmorpodcast.com/?feed=rss2').text\
	.replace('&#8211;', '–')\
	.replace('&#8217;', "'")\
	.replace('&#8220;', '"')\
	.replace('&#8221;', '"')

def rss_to_episode(item_xml):
	episode = { property_[0]: property_[2] for property_ in property_pattern.findall(item_xml) }
	enclosures = enclosure_pattern.findall(item_xml)
	if enclosures:
		episode['enclosure'] = enclosures[0]
	return episode

feed_episodes = [ rss_to_episode(item) for item in item_pattern.findall(hpmor_feed) ]
neiac_episodes = [ episode for episode in feed_episodes if ('Not Everything Is A Clue'.lower() in episode['title'].lower()) ]

def episode_to_rss(episode):
	title = episode['title'][len('Not Everything is a Clue'):].strip(' -–')
	chapters = chapter_pattern.findall(title)
	chapters = chapters[0] if chapters else None
	title = f"Chapters {chapters[0]}–{chapters[1]}" if chapters else title

	description_paragraphs = [p[2] for p in property_pattern.findall(episode['content:encoded']) if p[0] == 'p']
	cleaned_paragraph = property_pattern.sub(r'\3', description_paragraphs[0])
	description = desc_chapter_pattern.search(cleaned_paragraph)
	if description:
		description = description[0]
	else:
		description = cleaned_paragraph.split('.')[0]
	description = desc_pattern.sub('', description)

	encoded = '\n\t\t\t\t'.join([ l.strip(' \t') for l in episode['content:encoded'].split('\n') ])
	encoded = encoded.replace('<![CDATA[', '<![CDATA[\n\t\t\t\t').replace('\t]]>', ']]>')

	return f"""
		<item>
			<title>{title}</title>
			<link>{episode['guid']}</link>
			<guid isPermalink="true">{episode['guid']}</guid>
			<pubDate>{episode['pubDate'][:-12]}:00:00 +0000</pubDate>
			<content:encoded>{encoded}</content:encoded>
			<description>{description}.</description>
			<itunes:subtitle>{description}.</itunes:subtitle>
			<itunes:summary>{description}.</itunes:summary>
			<itunes:author>Eneasz Brodski</itunes:author>
			{episode['enclosure']}
			<itunes:duration>{episode['itunes:duration']}</itunes:duration>
		</item>
""".strip('\n')

new_line = '\n'

feed = f"""
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
	xmlns:content="http://purl.org/rss/1.0/modules/content/"
	xmlns:dc="http://purl.org/dc/elements/1.1/"
	xmlns:atom="http://www.w3.org/2005/Atom"
	xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd">
	<channel>
		<title>Not Everything is a Clue</title>
		<atom:link href="https://gorkyr.github.io/Custom-Podcast-Feeds/not-everything-is-a-clue.rss" rel="self" type="application/rss+xml" />
		<link>http://www.hpmorpodcast.com</link>
		<description>Join Eneasz and Steven for a very, very long adventure into another Rationali Fic — Worth the Candle, by Alexander Wales! Eneasz will play the role of the tour guide while doing his best to not spoil any of the surprises and Steven will play the seasoned adventurer who is new to this particular work.</description>
		<lastBuildDate>{neiac_episodes[0]['pubDate'][:-12]}:00:00 +0000</lastBuildDate>
		<language>en-US</language>
		<itunes:summary>Join Steven and Brian for a very, very long adventure into another Rational Fic — Worth the Candle, by Alexander Wales!</itunes:summary>
		<itunes:author>Eneasz Brodski &amp; Steven Zuber</itunes:author>
		<image>
			<title>Not Everything is a Clue</title>
			<url>https://i.imgur.com/CiaYGzR.png</url>
			<link>http://www.hpmorpodcast.com</link>
		</image>
		<itunes:image href="https://i.imgur.com/CiaYGzR.png"/>
		<itunes:category text="Arts">
			<itunes:category Text="Books"/>
		</itunes:category>
		<itunes:explicit>yes</itunes:explicit>

{new_line.join((episode_to_rss(episode) for episode in neiac_episodes))}
	</channel>
</rss>
""".strip('\n')

with open('not-everything-is-a-clue.rss', 'w', encoding='utf-8') as feed_file:
	feed_file.write(feed)