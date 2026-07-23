# Test Course Reset Utility

This is a small python tool I made to make it easier to reset a test course in Canvas. This tool was designed with Canvas admins in mind, so people with the other roles may experience issues using this tool.

## Getting Started

- Download the current release version for your computer from the [releases page](https://github.com/siekmang/test-course-reset/releases).
  - If you are on Windows of Linux, double-clicking the downloaded file should open.
  - If you are on Mac, you may need to open up a terminal and run the follow commands to remove the macOS flags about it coming from an unverified developer:
    ```
      cd <folder where your download landed>
      chmod +x test_course_reset-macos-universal
      xattr -d com.apple.quarantine test_course_reset-macos-universal
    ```
- Once open, click the 'Configuration' button. From here, you will need to enter your institution's subdomain, an access key, an ID for your test course and an ID from a course you'd want to pull content in from. These can be changed later.
- With your configuration set, you are then able to use the Course Reset buttons. Pressing these buttons will start the process of resetting your course. The app will showing a loading screen while it's waiting on a response from Canvas.
- Once you get the success notification, you can't user Ctrl/Cmd + Click on the text in the notification to open your test course at the content migrations screen to see it's progress.
  - If you open the course right after the success message, it may not have the course content populated yet. This is a limitation of Canvas' content migration tool, which is why the tool sends you to the content migration page in the course. That's where you'll be able to see the progress of your content migration.

## Terms

*Target Course* - This is the course you're going to be resetting
*Source Course* - This is the course you're that content is going to be migrated from into your test course

## Features
- The app does basic data validation and url stripping in the configuration step. This is pretty basic, but it's designed to try to catch potential errors with course IDs and access key. If you enter myschool.instructure.com for the subdomain, it will make an attempt to pull just the myschool out of it.
- Due to how Canvas handles course resetting, the reset tool will overwrite your old test course ID with a new one when the course resets, matching the new ID of your test course.
- Custom Course Reset is designed to give you a little more control over the process, you can either select to target your default test course or enter the name or id of the course you want to target, the same with the course you want to pull in content from.
  - If you use an ID, the tool will ask you to confirm that's correct.
  - If you use a course name, the tool will search your Canvas for matching courses and give you a choice of which course you want ot use.
  - If the course you're targetting for a reset doesn't contain the word test in it, the tool will ask you to confirm that you want to continue.
