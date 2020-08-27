# Temporal Measure of Software Similarity (TMOSS)

This repository contains a version of TMOSS, which is a method for analyzing intermediate student code. While this tool has been tested with MOSS as a backend software similarity detection software, any backend should be compatible.

This version of TMOSS has been tested to work on an Ubuntu machine.

## Setup

1. **Connecting the backend**: After you clone your repository, rename your moss backend directory to the ```bin``` directory. For example:

    ```
    code/
      bin/
        LICENSE
        moss        # the moss binary file
    ```

    You must download the MOSS binary from the [MOSS website](https://theory.stanford.edu/~aiken/moss/). We have provided a useful HTML interface (pymoss) for running and parsing the MOSS results, but this does not include the binary.

2. **Linking your data**:

   Your student data should be located in the ```data``` directory. Each course offering should be in its own sub-directory under ```data```. Online submissions are expected to be in their own ```online``` directory. If you do not have online or starter code directories, the script will still run.

    ```
    data/
        fall_2012/
          student_1/
            .git/
          student_2/
            .git/
          ...
        fall_2013/
          ...
        fall_2014/
          ...
    online/
        online_solution1/
            solutionFile.ext
        ...
    starter/
        starter_code1.ext
        ...
    ```

3. **Install dependencies**:

    ```
    sudo apt-get install python-matplotlib git
    ```

## Running the program

TMOSS is split into two steps:

1. Compute the top similarity score of all snapshots in all student repositories.

    The results of running TMOSS will be located in the ```out``` directory. The directory structure will be similar to ```data```.

2. Calculate the top match of each student.

    The top match results are located in ```out/<course_dir>/top_matches.csv``` and follow the following format:

    ```
    student_name,matched_student,snapshot_time_and_name,similarity_score
    ```

To run TMOSS:

```
python code/run.py
```

If you also want to plot a gumbel fit to your data afterwards, run:

```
python code/gumbel.py
```

The Gumbel script assumes your HEC and non-HEC results adhere to the following guidelines:

- Follow the format of ```top_matches.csv```, the unparsed results from running TMOSS.

- Have been looked through by a human to separate into the HEC and non-HEC groups.

- Are located in the out directory as follows:

    ```
    out/
      fall_2012/
        hec.csv
        non_hec.csv
        top_matches.csv       # the unparsed results from tmoss
      fall_2013/
        ...
      fall_2014/
        ...
    ```


## Citing this work

If you use TMOSS in your research, we ask that you please cite the following:

L. Yan, N. McKeown, M. Sahami, and C. Piech, “TMOSS: Using Intermediate Assignment Work to Understand Excessive Collaboration in Large Classes,” in Proceedings of The 49th ACM Technical Symposium on Computer Science Education (SIGCSE), February 2018.

[ACM library link](https://doi.org/10.1145/3159450.3159490)

Our paper is also available at [this link](http://stanford.edu/~yanlisa/publications/sigcse18_tmoss.pdf).

