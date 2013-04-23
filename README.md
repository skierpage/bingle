This is a tool to follow a Bugzilla atom feed, and import new bugs from the
feed into Mingle. More to come!

== Requirements ==
* feedparser: https://code.google.com/p/feedparser/
* requests: http://docs.python-requests.org/en/latest/

== To use ==
0. Prepare a Bugzilla atom feed to follow* 
1. Copy bingle.ini.example to bingle.ini
2. Update config vars to your own
3. $ python bingle.py

You can optionally configure bingle to run regularly (eg via cron) - it keeps
track of the last time it ran. If you use a bugzilla atom feed that uses bug
creation date as one of its params, bingle will update the timestamp to the
last time it ran, thereby fetching only bugs that have been added since the
last time bingle was executed.
