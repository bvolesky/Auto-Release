![Pipeline Image](pipeline.jpg)
# Auto-Release
This script automates an operational task pipeline by executing Maven commands and remote commands via PuTTy to generate stats for release review.

## Learnings:
For this particular task, I embarked on a "pie-in-the-sky" quest to create a streamlined and automated solution that could significantly enhance my workflow. This endeavor encompassed a multitude of intricate steps. Here are some steps involved:

Managing the interaction of 'git' operations with the commit, versioning, authentication, and tag systems.
Incorporating functionality to execute custom internal uniilities that necessitated secure user input.
Created a robust rollback mechanism for handling command failures.
Complined specific URLs with the requisite inputs while validation procedures for URLs and mappings.
Processed various forms of text, such as paths, URLs, and versioned JARs, while adhering to the same specification version.
Ensured scalability and multi-threaded efficiency.
Furthermore, I undertook the responsibility of securing and facilitating password management for Putty authentication, along with the execution of remote commands.

I am proud to report that not only did I achieve success in this endeavor, but I also played a pivotal role in assisting my teammates by saving them valuable time. This newfound efficiency allowed them to redirect their focus towards more significant and less repetitive tasks. As a direct result of these improvements, our business experienced heightened efficiency and a reduction in compute costs. This, in turn, enabled our team to align with bottom-line business objectives in a highly efficient and budget-conscious manner.

## Usage
1. Install Python from [Python Downloads](https://www.python.org/downloads/).
2. Clone the Repository - ```git clone https://github.com/bvolesky/Auto-Release.git```
3. Navigate to the Repository - ```cd <repository_folder>/Auto-Release```
5. Run the App - ```python Auto-Release.py```
