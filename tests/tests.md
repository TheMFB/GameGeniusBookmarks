# Here are the commands I used to do a quick test:

`bm ls`

`bm --which 01`
`bm 01 -d` - select bookmarks

- TODO(MFB):
__ handle_export_from_redis_to_redis_dump __
❌ Error running Redis command


- TODO(MFB): When we have an error:
__ create_bookmark_symlinks __
✅ Integrated workflow completed successfully!

- TODO(MFB): redis friendly converters


# Minimal Success:
- ls bookmarks (ALL search logic sound)
- track last used bookmark
- create bookmark from -p
    - navigational commands
    - bookmark search
- create bookmark from -b
- create bookmark from redis
- load old bookmarks states
- adding tags


- TODO(MFB): If we are not local, our dump should be the session_manager dump.

- TODO(MFB): Is there an issue with dry-run and then still trying to pull/save from Redis (if we are not local?)