
# aider is AI pair programming in your terminal

Aider is a command line tool that lets you pair program with LLMs,
to edit code stored in your local git repository.
Aider will directly edit the code in your local source files,
and [git commit the changes](https://aider.chat/docs/faq.html#how-does-aider-use-git)
with sensible commit messages.
You can start a new project or work with an existing git repo.
Aider is unique in that it lets you ask for changes to [pre-existing, larger codebases](https://aider.chat/docs/repomap.html).
Aider works well with GPT-4o, Claude 3 Opus, GPT-3.5
and supports [connecting to almost any LLM](https://aider.chat/docs/llms.html).

<p align="center">
  <img src="assets/screencast.svg" alt="aider screencast">
</p>

<p align="center">
  <a href="https://discord.gg/Tv2uQnR88V">
    <img src="https://img.shields.io/badge/Join-Discord-blue.svg"/>
  </a>
</p>

- [Getting started](#getting-started)
- [Features](#features)
- [Usage](#usage)
- [Tutorial videos](https://aider.chat/docs/install.html#tutorial-videos)
- [In-chat commands](#in-chat-commands)
- [Tips](#tips)
- [Installation](https://aider.chat/docs/install.html)
- [Connecting to LLMs](https://aider.chat/docs/llms.html)
- [LLM Leaderboards](https://aider.chat/docs/leaderboards/)
- [Voice-to-code](https://aider.chat/docs/voice.html)
- [Example chat transcripts](https://aider.chat/examples/)
- [FAQ](https://aider.chat/docs/faq.html)
- [Discord](https://discord.gg/Tv2uQnR88V)
- [Blog](https://aider.chat/blog/)


## Getting started

See the
[installation instructions](https://aider.chat/docs/install.html)
for more details, but you can
get started quickly like this:

```
$ pip install aider-chat

# To work with GPT-4o
$ export OPENAI_API_KEY=your-key-goes-here
$ aider

# To work with Claude 3 Opus:
$ export ANTHROPIC_API_KEY=your-key-goes-here
$ aider --opus
```


## Features

* Chat with aider about your code by running `aider <file1> <file2> ...` from the command line with set of source files to discuss and edit together. Aider lets the LLM see and edit the content of those files.
* Aider can write and edit code in most popular languages: python, javascript, typescript, php, html, css, etc.
* Aider works well with GPT-4o, Claude 3 Opus, GPT-3.5 and supports [connecting to almost any LLM](https://aider.chat/docs/llms.html).
* Request new features, changes, improvements, or bug fixes to your code. Ask for new test cases, updated documentation or code refactors.
* Aider will apply the edits suggested by the LLM directly to your source files.
* Aider will [automatically commit each changeset to your local git repo](https://aider.chat/docs/faq.html#how-does-aider-use-git) with a descriptive commit message. These frequent, automatic commits provide a safety net. It's easy to undo changes or use standard git workflows to manage longer sequences of changes.
* You can use aider with multiple source files at once, so aider can make coordinated code changes across all of them in a single changeset/commit.
* Aider can [give the LLM a map of your entire git repo](https://aider.chat/docs/repomap.html), which helps it understand and modify large codebases.
* You can also edit files by hand using your editor while chatting with aider. Aider will notice these out-of-band edits and keep up to date with the latest versions of your files. This lets you bounce back and forth between the aider chat and your editor, to collaboratively code with an LLM.
* You can add images files to your chat if you are working with a vision capable OpenAI model (GPT-4o, GPT-4 Turbo, etc).


## Usage

Run `aider` with the source code files you want to edit.
These files will be "added to the chat session", so that the LLM can see their
contents and edit them according to your instructions.

```
aider <file1> <file2> ...
```

Be selective, and just add the files that the LLM will need to edit.
If you add a bunch of unrelated files, the LLM can get overwhelmed
and confused (and it costs more tokens).
Aider will automatically
share snippets from other, related files with the LLM so it can
[understand the rest of your code base](https://aider.chat/docs/repomap.html).

You can also just launch aider anywhere in a git repo without naming
files on the command line.  It will discover all the files in the
repo.  You can then add and remove individual files in the chat
session with the `/add` and `/drop` chat commands described below.
If you or the LLM mention any of the repo's filenames in the conversation,
aider will ask if you'd like to add them to the chat.

Aider also has many other options which can be set with
command line switches, environment variables or via a configuration file.
See `aider --help` for details.


## In-chat commands

Aider supports commands from within the chat, which all start with `/`. Here are some of the most useful in-chat commands:

* `/add <file>`: Add matching files to the chat session, including image files.
* `/drop <file>`: Remove matching files from the chat session.
* `/undo`: Undo the last git commit if it was done by aider.
* `/diff`: Display the diff of the last aider commit.
* `/run <command>`: Run a shell command and optionally add the output to the chat.
* `/voice`: Speak to aider to [request code changes with your voice](https://aider.chat/docs/voice.html).
* `/help`: Show help about all commands.

See the [full command docs](https://aider.chat/docs/commands.html) for more information.


## Tips

* Think about which files need to be edited to make your change and add them to the chat.
Aider can help the LLM figure out which files to edit all by itself, but the most efficient approach is to add the needed files to the chat yourself.
* Large changes are best performed as a sequence of thoughtful bite sized steps, where you plan out the approach and overall design. Walk the LLM through changes like you might with a junior dev. Ask for a refactor to prepare, then ask for the actual change. Spend the time to ask for code quality/structure improvements.
* Use Control-C to safely interrupt the LLM if it isn't providing a useful response. The partial response remains in the conversation, so you can refer to it when you reply to the LLM with more information or direction.
* Use the `/run` command to run tests, linters, etc and show the output to the LLM so it can fix any issues.
* Use Meta-ENTER (Esc+ENTER in some environments) to enter multiline chat messages. Or enter `{` alone on the first line to start a multiline message and `}` alone on the last line to end it.
* If your code is throwing an error, share the error output with the LLM using `/run` or by pasting it into the chat. Let the LLM figure out and fix the bug.
* LLMs know about a lot of standard tools and libraries, but may get some of the fine details wrong about APIs and function arguments. You can paste doc snippets into the chat to resolve these issues.
* The LLM can only see the content of the files you specifically "add to the chat". Aider also sends a [map of your entire git repo](https://aider.chat/docs/repomap.html). So the LLM may ask to see additional files if it feels that's needed for your requests.

## Example chat transcripts

[The example transcripts page](https://aider.chat/examples/) shows how you can chat with aider to write
and edit code.

## Installation

See the [installation instructions](https://aider.chat/docs/install.html).

## FAQ

For more information, see the [FAQ](https://aider.chat/docs/faq.html).

## Kind words from users

* *The best AI coding assistant so far.* -- [Matthew Berman](https://www.youtube.com/watch?v=df8afeb1FY8)
* *Hands down, this is the best AI coding assistant tool so far.* -- [IndyDevDan](https://www.youtube.com/watch?v=MPYFPvxfGZs)
* *Aider ... has easily quadrupled my coding productivity.* -- [SOLAR_FIELDS](https://news.ycombinator.com/item?id=36212100)
* *It's a cool workflow... Aider's ergonomics are perfect for me.* -- [qup](https://news.ycombinator.com/item?id=38185326)
* *It's really like having your senior developer live right in your Git repo - truly amazing!* -- [rappster](https://github.com/paul-gauthier/aider/issues/124)
* *What an amazing tool. It's incredible.* -- [valyagolev](https://github.com/paul-gauthier/aider/issues/6#issue-1722897858)
* *Aider is such an astounding thing!* -- [cgrothaus](https://github.com/paul-gauthier/aider/issues/82#issuecomment-1631876700)
* *It was WAY faster than I would be getting off the ground and making the first few working versions.* -- [Daniel Feldman](https://twitter.com/d_feldman/status/1662295077387923456)
* *THANK YOU for Aider! It really feels like a glimpse into the future of coding.* -- [derwiki](https://news.ycombinator.com/item?id=38205643)
* *It's just amazing.  It is freeing me to do things I felt were out my comfort zone before.* -- [Dougie](https://discord.com/channels/1131200896827654144/1174002618058678323/1174084556257775656)
* *This project is stellar.* -- [funkytaco](https://github.com/paul-gauthier/aider/issues/112#issuecomment-1637429008)
* *Amazing project, definitely the best AI coding assistant I've used.* -- [joshuavial](https://github.com/paul-gauthier/aider/issues/84)
* *I absolutely love using Aider ... It makes software development feel so much lighter as an experience.* -- [principalideal0](https://discord.com/channels/1131200896827654144/1133421607499595858/1229689636012691468)
* *I have been recovering from multiple shoulder surgeries ... and have used aider extensively. It has allowed me to continue productivity.* -- [codeninja](https://www.reddit.com/r/OpenAI/s/nmNwkHy1zG)
* *I am an aider addict. I'm getting so much more work done, but in less time.* -- [dandandan](https://discord.com/channels/1131200896827654144/1131200896827654149/1135913253483069470)
* *After wasting $100 on tokens trying to find something better, I'm back to Aider. It blows everything else out of the water hands down, there's no competition whatsoever.* -- [SystemSculpt](https://discord.com/channels/1131200896827654144/1131200896827654149/1178736602797846548)
* *Best agent for actual dev work in existing codebases.* -- [Nick Dobos](https://twitter.com/NickADobos/status/1690408967963652097?s=20)
