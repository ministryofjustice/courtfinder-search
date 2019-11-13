Dependencies
1. Docker
2. Gatling 


### Running Gatling tests locally

1. Start docker daemon 
2. From the performance-tests directory, run below to build your local docker container

    ```
    docker build -t ctfgatling:local . 

    ```


3. From the performance-tests directory, run gatling scripts against docker image
   ```
 docker run --rm -e APP_URL=https://staging.courttribunalfinder.service.gov.uk -e APP_NAME=example_username -e APP_PASSWORD=example_password -v `pwd`/src/test/resources:/opt/gatling/conf -v `pwd`/src/test/scala/simulations:/opt/gatling/user-files/simulations -v `pwd`/results:/opt/gatling/results -v `pwd`/data:/opt/gatling/data ctfgatling:local -s simulations.StaffPerformance
   ```

Note: Replace 'example_username' and 'example_password' with valid credentials for staff login. If running the public app, remove '-e APP_NAME=example_username -e APP_PASSWORD=example_password'.

    
4. Reports folder will be created once tests successfully ran