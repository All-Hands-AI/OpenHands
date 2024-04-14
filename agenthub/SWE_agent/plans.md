# Things that need to be done for SWE-Agent

## 1. Add in all of the following commands to ACI
```
'search_for': {
    'params': '<keywords>',
    'description': 'Will allow you to search your working directory for files and folders that match your <keyword>.',
}

'edit ': {
    'params': '<filename>',
    'description': 'This will allow you to modify files within your working directory. Usage: "edit example.txt" -> opens the example.txt file and shows the first 100 lines',
},

'goto': {
    'params': '<line_num>',
    'description': 'This will allow you to go through a file to any line. Usage: "Goto 124" -> returns lines 124-224 within current file',
},

'scroll_up': {
    'params': '',
    'description': 'When you are in a file you can see the 100 lines above your current view. Usage: "scroll_up" -> returns the 100 lines above what you were reading',
},

'scroll_down': {
    'params': '',
    'description': 'When you are in a file you can see the 100 lines below your current view. Usage: "scroll_down" -> returns the 100 lines below what you were reading',
},

'modify': {
    'params': '<start_line>:<end_line> "<replacement>"',
    'description': 'This will make changes to a file by deleting all lines from <start_line> to <end_line> and replacing them with <replacement>',
}

```
## 2. Add linter to check code edits before modifying file
