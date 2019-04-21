# Wigle
An attempt to build a search engine from scratch....

# General approach
Crawl pages, use words to create reverse index, rank pages based on keywords & 
overall page reputation, yields best results when asked.

# Questions

> 
Responsiveness
Reputation
Multiple words
Speed
Seed links
>

if multi-word isn't there, try subsets (up to 8 words)

!Add second level dictionary to compress master
!Figure out fast batching
!Fix bug for exact matches on multi-words e.g. "South America"
!Half memory size by recording url extension w/o base