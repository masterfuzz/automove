[![Build Status](https://travis-ci.org/masterfuzz/automove.svg?branch=master)](https://travis-ci.org/masterfuzz/automove)

Automove
========

Organizes files in a directory structure based on 'tags' from a database lookup.

## Configuration
Behaviour is configured by the default configuration file, or one specified on the command line with `automove -c conf.yaml`

The lookup order for configuration is as follows:
`./automove.yaml`, `$XDG_CONFIG_HOME/automove/conf.yaml`, `$HOME/.config/automove/conf.yaml`, `/etc/automove/conf.yaml`

### Example Configuration
```yaml
# List of paths to scan for files
Sources:
-  /path/to/unorganized/files

# List of destinations for organized files
Destinations:
  DEST_NAME:
    db: db name
    path:  /path/to/destination
    file type: file type to check
    org: /tag/organization

# List of database modules to use for tagging
Databases:
  a_database:
    - a_database_module_name

Transfer:
  dry run: false      # Dry run will not copy or delete files when true
  make dir: true      # Make tag directories when necessary
  overwrite: false    # Overwrite files in destination
  delete: false       # Delete files from source
  verify: true        # verify transfer (with cmp)

Notifications:
  when no tags: true  # Notify when no tags found for a file
  summary: true       # Only notify once with a summary
  module: a_module    # Optional. Otherwise logs to std out
  module parameters:  # Notification module can optionally take parameters
    param: value
```


