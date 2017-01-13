# Upgrading Legacy Python Systems to Python 3

This document assumes you have a large codebase which you want to upgrade from Python 2 to a modern version of Python. It's highly opinionated, and intends to give _a_ way of upgrading that will be effective for many codebases.

## Prerequisites

1. You should have a fairly good test suite for this application, such that if it passes, you can have reasonably good assurance that no bugs were introduced in a refactoring or similar change.
2. You should have some familiarity with the Python build ecosystem. In particular, experience with [`tox`](http://tox.readthedocs.io/en/latest/) and [`flake8`](http://flake8.pycqa.org/en/latest/) would be useful. Experience with [`six`](https://pythonhosted.org/six/).
3. You should have a fair amount of time to do slightly tedious, if mindless work. For example, it's reasonable to do a lot of the more tedious parts of this while watching television or listening to podcasts.
4. Some understanding of the differences between Python 2 and Python 3. See Appendix 1.
5. You should have already upgraded your code to Python 2.7. This will allow you to use all the backports from Python 3 including new syntaxes. It's _much_ easier than upgrading to Python 3, so if you haven't already done this, there are probably larger issues that need fixed than upgrading to Python 3.

## Linting

The first thing you want to do with your codebase is to identify the easily detected issues, and prevent backsliding on fixes you've already deployed.

Add a `tox.ini` file to your repository. [Tox](https://tox.readthedocs.io/en/latest/) is a build automation program that allows you to specify environments you'd like your code to run in. 

```
[tox]
envlist = {py27,py35}-flake8

[testenv:flake8]
deps = flake8
skip_install = True
commands =
  flake8 {posargs:relative/path/to/app/code}

[flake8]
ignore = E999,.. # [errors to ignore]
exclude = *nolint.py,migrations*  # paths to ingore
show-source = true
```

This will run the flake8 linter under both Python 2 and Python 3 when you run `tox`. If you don't want to fix some linting rules, add them to the `ignore` section. This will find two kinds of Python 3 errors:
- Syntax errors (`print "something"`, `except Foo, bar:`, etc.).
- Undefined variable names that were built-in to Python 2 (`unicode`, `xrange`, etc). Note that some previously-builtin methods have been moved (in particular `reduce` was moved to `functools.reduce`).



## Appendix 1: Backwards-incompatible changes from Python 2.7 to Python 3

The [main breaking changes](https://docs.python.org/3.0/whatsnew/3.0.html) were as follows:

### Unicode
The default type for textual data is `unicode`. Bytestrings must be annotated with a `b'string'`, and `bytes.__getitem__` now returns an integer instead of a string of length 1.

The `unicode` type was initially introduced into python with a lot of hacky implicit decoding. Loosely speaking, any time that `unicode` and `bytes` needed to be combined, an implicit call to `.decode('ascii')` was made on the bytes object. Any time `unicode` needed to be written to a bytestream, an implicit call to `.encode('ascii')` was made. This meant that code could look fine, and run fine as long as it was being given only data from anglophone countries which contained no emojis. If those assumptions were violated, then 💣💥 `Unicode{De,En}codeError`.

Python 2.7 introduced some compatibility libraries with Python 3, most importantly `io.BytesIO` and `io.StringIO`, which fail when given the wrong types.

### Miscellaneous Changes

- *Many* libraries were moved or removed. Compatibility shims have been written for most of these. The primary library for this use is `six`, which allows running code on python 2 and python 3 by using the correct `six` idiom. Their [docs](https://pythonhosted.org/six/) are worth skimming in their entirety. These import moves and removals are covered in the linting section above.
- The `long` and `int` types were unified prior to 2.7 for most use cases, but in Python 3, the `long` type has been completely removed.
- The syntax for using metaclasses changed. You can generate compatible code by having your class inherit from `six.with_metaclass(MyMetaClass)`.
- The `except ExceptionClass, exception_instance:` syntax was removed.
- `print` was turned from a statement to a function like any other. You can (and should) get this behavior in Python 2 by using `from __future__ import print_statement`
- Implicit relative imports are no longer allowed. All imports must be absolute (relative to the root `PYTHONPATH`), or _expclitly_ relative `from ..foo import bar`. You can (and should) get this behavior in Python 2 by using `from __future__ import absolute_import`.
- `range` now behaves like `xrange` used to. It does not instantiate a list, and can be iterated over with a constant amount of memory.
- `izip`, `ifilter` and `imap` have been removed from the `itertools` package and replaced `zip`, `filter` and `map`. In order to get the old behavior, you need to explicitly evaluate them as a list, like `list(map(foo, bars))`.
- Similarly, `dict.{view,iter}_{keys,values,items}` have been merged into `dict.keys`, `dict.values` and `dict.items`. These are _views_ on the underlying hash table, and behave essentially like the old `dict.view_*` methods.
- Division of integers now converts to float, so `1/2 == 0.5`. You can (and should) get this behavior in Python 2 by using `from __future__ import division`.
- Functions can no longer include tuples to be unpacked, eg `def foo(bar, (baz, quux)):`.

## Appendix 2: Monday-morning quarterbacking on Python 3

First note, I very genuinely think Python 3 is now a substantially better language than older versions of Python. (This was debatable until 3.5, which introduced some great features. 3.6 is _leagues_ better than 2.7). I have a great deal of respect for the Python Core team, who gave this process a lot of thought, and devoted significant parts of their careers to making Python better. They also avoided many of the problems that the Perl team had with the Perl 6 launch: no one can accuse them of letting the perfect be the enemy of the good and taking forever to ship.

That said, I've given the Python 2/Python 3 upgrade process a lot of thought, and (with hindsight) there are a number of ways it could have been handled better. Other programming languages or large frameworks should keep these in mind.

### Tying a lot of breaking changes together complicates upgrades

Python 3 did three main things:
- Fixed most issues with handling of unicode, treating that as the primary reason for interacting with streams.
- Made working with bytes somewhat harder.
- Changed a lot of other stuff that wasn't hard, but is tedious to fix. Library moves, syntax changes, basically raison d'être of `six`. Simple stuff, but across hundreds of millions of lines of code, that's a _lot_ of work.

That was _pretty much_ it. There were a few other nice features like dictionary comprehensions and the like that were backported to Python 2.7. This led to a situation where, for several years, no one had an incentive to upgrade:
- Developers of libraries who deal with lots of binary data found python 3 harder to use.
- For a while, it was literally impossible to write code that was compatible with both of them, until [PEP 414](https://www.python.org/dev/peps/pep-0414/) came out in python 3.3.
- Most other library developers didn't see any of their users upgrading, so didn't care to.

I think the main issue here was there the complicated and intricate changes required to correctly handle unicode were _tied_ to a bunch of boring changes like moving imports around and hunting for print statements. Programmers are pretty good at boring repetitive tasks (though we hate them), and we're pretty good at cognitively taxing tasks (which we sort of like, even if we curse them under our breath). This whole setup framed the python 3 upgrade as a _difficult_, _boring_ task. 

To recall, the timeline was
- 2008: Python 2.6 and Python 3 were essentially released at the same time, within two months of each other.
- 2010: Python 2.7 is released 18 months later, backporting the main useful features from 3, and adding some compatibility shims like `from __future__ import print_statement`.
- 2012: Python 3.3 is released, the first truly usable version of python 3.

During those ~4 years, essentially no progress was made by users of the language in porting to Python 3. Entire companies were founded and failed writing python 2 code. Codebases didn't deal with any of the compatibility issues. In the intervening 4 years, Python 3 has started to come into its own. Most major libraries now support both versions, and useful new features have been added to the language. I'd venture most new codebases are being written in Python 3, but an enormous amount of work went into writing libraries using Python 2 idioms, that will now need to be ported.

I think Python 2.7 should have been devoted _solely_ to boring breaking changes:
- Library renames.
- Removals.
- Rename `unicode` to `str` and `str` to `bytes`.
- `from __future__ import unicode_literals, print_function, division, absolute_import` are the default.
- Remove optional syntaxes in catching exceptions, rasing exceptions, etc. from the grammar, allowing only the python-3 compatible ones.

This would seriously throttle adoption of 2.7, but that was the version that the core developers didn't care much about. Python 3 was the future, and as written, Python 2.7 let you write code which was _mostly_ Python 3 compatible _if you were meticulous_. But bizarro-2.7 would have meant:
- Converting from 2.6 to bizarro-2.7 could have been _completely_ automated. 2.6to2.7 might have actually worked out of the box, unlike 2to3.
- It would be possible to write custom import hooks to use 2.6-only libraries in 2.7, since the underlying language semantics would be the same, and only the "frontend" was different.
- By the time Python 3 was usable, the _only_ thing that would need to be solved is ferreting out tricky implicit encoding. Many libraries would actually just work out of the box on both 2.7 and 3.X.
- The end-of-life for python 2.6 in 2013 would have caused compliance-focused IT departments to bite the bullet and do the tedious but reliable work of changing over to the new imports and syntaxes.

And then, three years later? We'd have a _lot_ more code that runs on Python 3 without hacks like `six`, and many companies would have already switched over. There'd be much less porting left to do, and it would be focused in one main area: text encoding and decoding. To the extent that people were still writing python-3-incompatible code, it would be much less incompatible.

In fairness, I think this is what the core maintainers were _trying_ to do with python 3.0 and 2to3. As I understand it, the hope was that 2.7 would be a bridge to python 3, and 2to3 would let organizations and libary maintainers leave Python 2 behind once Python 3 was ready. 

And also, hindsight is 20/20, so I'm in no way claiming that I would have made better decisions if I were in Guido's shoes. That said, I do think it's worthwhile to think through what went wrong and what went right about a big transition like this, so that other communities can learn from it.