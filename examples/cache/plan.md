# Plan: A cache for the course search

## The occasion

- Audience: the platform team, two managers from student services, and the head of registration
- Occasion: the monthly review of the platform team
- Time: 12 minutes
- Questions: after the talk
- Room: a small meeting room with a screen, lights on
- Online: no

## The kind of talk

- Kind: small meeting
- Pure story: no
- Call to action: no
- Shape: asymmetric hourglass

## The audience

Engineers who know the database, and managers who decide what the team builds next. The managers matter
most, because they choose the next project. Each slide still defines its terms for them, such as "cache"
and "hit rate".

## The headline

A one-minute copy of each search page cut the wait at nine from eight seconds to under one.

## The action

No call to action. The managers should leave knowing that the cache works, and why the timetable page is
next.

## The opening statement

Every morning at nine, three thousand students open the course search, and the page slows to a crawl. We
cut that wait to under a second, and the fix came from one fact about how students search.

## The closing statement

Search at nine now takes under a second, because most students ask for the same twenty courses, and a
one-minute copy answers them all. Next we'll give the timetable page the same cache.

## The outline

### Students wait eight seconds at nine

- 3,000 searches in ten minutes, 8 seconds each, 1 in 5 students gives up
- Story: a student who retried the search four times and missed a seat
- Must show: the timing chart of one search, from the incident report

### The database repeats one job

- Each search reads the same course rows again
- Most students search for the same twenty courses
- Figure: one bar for each step of a search, the database read the longest

### A copy for one minute

- Keep each result page for one minute, and clear it when a course changes
- The hit rate sets the load, reads = (1 − h) × searches
- Story: the first try with ten-second copies, which missed most searches

### The wait fell to under a second

- Search time at nine, before and after, for four weeks
- Help tickets fell by half
- Must show: the chart of search time from the dashboard

## The questions

- Q: Can a student see a wrong seat count?
  A: For at most a minute, and a course change clears the copy at once.
- Q: What does the cache cost?
  A: About two hundred lines of code and some memory on each server, with no new server.
