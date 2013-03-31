# Seamless Dropbox

Wrapper of some parts of Dropbox API in File Objects interface*.

### Motivation

The goal of the module is to provide smooth way to use scripts written on desktop system using absolute paths on other platforms that have access to dropbox files only by its API. Like iOS with Pythonista app.

User needs only to *import open from seamless_dropbox* (thus overwriting standard open).

### Implemented

- close
- read
- readline
- readlines
- write
- writelines
- 'with' statement (\__enter__ & \__exit__)

*Not every method from File interface is implemented, only those for writing and reading. Also not every optional argument has sense in context of Dropbox, in that case value for this argument can be previded but does nothing.
