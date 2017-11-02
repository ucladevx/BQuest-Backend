# Pick My Bruin

## Setup
1. Install `docker` and `docker-compose`. 
2. run `make build && make run` in the root directory (this one)


## Project Organization

Simplified tree diagram
``` /usr/bin/tree
.  # Contains docker setup and Makefile
├── docker-compose.yml  # defines setup of PostgreSQL and Django
├── Dockerfile  # defines pickmybruin/backend Docker image
├── initialize.sh  # sets up Django container (runs migrations and then boots server)
├── Makefile  # contains very useful helper commands
└── src  # Contains all Django code
    ├── pickmybruin  # Contains code relating to the entire website
    │   ├── keys.py  # put confidential info in here
    │   ├── settings.py  # global settings (please keep confidential info out of here)
    │   ├── urls.py  # global URLs (usually imports app URLs too)
    └── users  # One app for just users
        ├── admin.py  # sets up /admin pages
        ├── models.py  # contains class declarations and methods
        ├── serializers.py  # contains serializers for classes 
        ├── tests.py  # necessary (pls)
        ├── urls.py  # sets up app specific URLs
        └── views.py  # sets up responses to URLs
```

## Makefile commands
- `make build` creates the `pickmybruin/backend` image
- `make run` starts up the PostgreSQL and Django containers
- `make restart` restarts the Django container (useful when you edit code)
- `make ssh` starts a bash session in the latest Django container
- `make run_command` runs a command inside the latest Django container
    - `make run_command cmd="echo hi"` will run `echo hi` inside the latest Django container
- `make shell` starts a `manage.py shell_plus` inside the latest Django container
    - If you don't know what this means, that's fine

## How to add a new app
1. Run `make run_command cmd="src/manage.py startapp $APPNAME`
    - This creates a new skeleton folder for your new app
2. YOU MUST ADD THIS APP TO `src/pickmybruin/settings.py` `INSTALLED_APPS` FOR THE APP TO BE DISCOVEREDR
    - `'users',` adds the `users` app to the Django project.  Big surprise.
3. Add your code
4. Add tests to `tests.py`
5. Add your models to `admin.py`
6. Import your urls.py in `src/pickmybruin/urls.py`
7. Run the tests
8. Submit a PR


## API
### Create new user
  POST /users/
  ```
      {
          "email": "<EMAIL>",
          "password": "<PASSWORD>"
      }
  ```
  returns 
  ```
      {
          "user_id": <PROFILE_ID>
      }
  ```
  send a verification email with a link: "https://pickmybruin.com/verify_user?user_id=<PROFILE_ID>&code=<VERIFICATION_CODE>"

### Verify user
  POST /users/<USER_ID>/verify
  ```
      {
          "code": "<VERIFICATION_CODE>"
      }
  ```
  returns  
  ```
      {
          "user_id": <PROFILE_ID>
      }
  ```

### Login
  POST /o/token (login)
  ```x-www-form-urlencoded
      grant_type:password
      username:<USER_EMAIL>
      password:<USER_PASSWORD>
      client_id:web
      client_secret:<CLIENT_SECRET> // Note: the CLIENT_SECRET is a hardcoded field you need to get from your backend
  ```
  returns 
  ```
      {
          "access_token": "<ACCESS_TOKEN>",
          "expires_in": 36000,
          "token_type": "Bearer",
          "scope": "read write groups",
          "refresh_token": "<REFRESH_TOKEN>"
      }
  ```

### Authorization
  Authorization done over headers  
  Authorization: "Bearer <ACCESS_TOKEN>"

### Get own user
  GET /users/me/  
  returns
  ```
      {
          "id": <PROFILE_ID>,
          "user": {
              "id": <USER_ID>,
              "first_name": "<USER_FIRST_NAME>",
              "last_name": "<USER_LAST_NAME>",
              "email": "<USER_EMAIL>"
          },
          "year": "<YEAR>",
          "verified": "<VERIFIED>",
          "date_created": "<DATE_CREATED_ISO8601>"
      }
  ```

### Get specific user (not sure if needed)
  GET /users/<PROFILE_ID>/  
  return is same as /users/me/  

### Update own user
  PATCH /users/me/  
  schema is same as /users/me/, but will update subfields (don't change the id please)  
  return is same as /users/me/  

### Get own mentor
  GET /mentors/me/  
  returns  
  ```
      {
          "major": "<MAJOR>",
          "classes_taken": [
              <CLASSES_TAKEN> ...
          ],
          "date_created": "<DATE_CREATED_ISO8601>"
      }
  ```

### Activate own mentor
  POST /mentors/me/
    - create mentor it doesn't exist
    - activate mentor if it does exist
  returns same as /mentors/me/  

### Update own mentor
  PATCH /mentors/me/  
  schema is same as /mentors/me/, but will update subfields (don't change the id please)  
  return is same as /mentors/me/  

### Get possible majors
  GET /majors/  
  returns  
  ```
      {
          "majors": [
              <MAJORS>...
          ]
      }
  ```

### Get possible years
  GET /years/  
  returns  
  ```
      {
          "years": [
              <YEARS>...
          ]
      }
  ```

### Search for mentors
  GET /mentors/?major=<MAJOR_ID>  
    - only returns active mentors
    - excludes yourself
    - sort by year decreasing for now
    - no pagination for now
  returns   
  ```
      {
          "mentors": [
              <MENTORS>... // same as /mentor/me/ format
          ]
      }
  ```

### Get specific mentor
  GET /mentors/<MENTOR_ID>/  
  return is same as /mentors/me/  


### Send mentor a request
  POST /requests/<MENTOR_ID>/  
  ```
      {
          "message": "<EMAIL_BODY>"
      }
  ```

## Current Database Schema (Will probably be outdated soon)

### NOTE: you don't really need to understand this, but this is how Django will create tables for the models


#### User Table

id | email | first_name | last_name | (salted and hashed) password 
--- | --- | --- | --- | --- 
1 | me@marktai.com | Mark | Tai | verysecurepassword 
2 | you@marktai.com | John | Doe | corgisarecute 


#### Profile Table

id | user_id | bio 
--- | --- | --- 
1 | 1 | Let me know if these examples suck 
2 | 2 | [marktai.com/#corgis](https://www.marktai.com/#corgis) for all your corgi needs 


#### Major Table

id | name 
--- | --- 
1 | CS 


#### Mentor Table

id | profile_id | major_id | bio 
--- | --- | --- | --- 
1 | 2 | 1 | I will teach you the ways of corgis 


