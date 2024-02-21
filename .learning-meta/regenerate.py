#!/usr/bin/env python
# Copyright 2024 NetBox Labs Inc
"""Generate repo content from templates."""

from datetime import datetime
import feedparser
import jinja2
import logging
import os
import requests
import sys


TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
REPO_ROOT_DIR = os.path.join(os.path.dirname(__file__), "..")

def main():
    """Regenerate the monorepo static contents using templates."""
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting")

    # Check everything exists that we need
    if os.path.exists(TEMPLATE_DIR) is False:
        logging.error("Template directory %s does not exist", TEMPLATE_DIR)
        sys.exit(1)

    # Setup Jinja2
    j2_loader = jinja2.FileSystemLoader(
        [os.path.join(os.path.dirname(__file__), TEMPLATE_DIR)]
    )
    j2_env = jinja2.Environment(loader=j2_loader)

    # Get source data
    blog_articles = list_blog_articles()
    oss_releases = list_netbox_oss_releases()
    youtube_videos = list_youtube_videos()

    # Render the README.md
    template = j2_env.get_template("README.md.j2")
    # Render the template
    generated_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    rendered = template.render(generated_at=generated_at, blog_articles=blog_articles, oss_releases=oss_releases, youtube_videos=youtube_videos)

    # Write the rendered template to the destination file
    dest_file = "README.md"
    dest_file_path = os.path.join(REPO_ROOT_DIR, dest_file)
    logging.info("Writing %s", dest_file_path)
    with open(dest_file, "w") as f:
        f.write(rendered)

    logging.info("Done")
    sys.exit(0)


def list_blog_articles() -> list[dict]:
    logging.info("Getting Netbox Labs blog articles")
    feed = feedparser.parse("https://netboxlabs.com/feed/")
    return feed.entries

def list_netbox_oss_releases() -> list[dict]:
    logging.info("Getting Netbox OSS releases")
    feed = feedparser.parse("https://github.com/netbox-community/netbox/releases.atom")
    return feed.entries

def list_youtube_videos() -> list[dict]:
    logging.info("Getting Youtube videos")
    feed = feedparser.parse("https://www.youtube.com/feeds/videos.xml?channel_id=UCs5FgE5p03tP-8InKVIojdw")
    return feed.entries


if __name__ == "__main__":
    main()
