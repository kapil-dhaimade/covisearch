var app = angular.module('myApp', []);
app.controller('formCtrl', function ($scope, $http, $timeout) {
    const api_base_url = "https://asia-south1-covisearch2.cloudfunctions.net/covisearchapi?";
    // $scope.master = {
    //     city: "Mumbai", 
    //     resource: {
    //         'displayName': 'Oxygen',
    //         'value': 'oxygen'
    //     }
    // };

    $http.get('../data/cities.txt').then(function (response) {
        $scope.cityList = response.data;
    });
    // $scope.cityList = ["Mumbai", "Delhi"];

    $scope.init = function () {
        $scope.pageNumber = 0;
        $scope.retryCount = 3;
        $scope.dataFetched = false;
    };

    $scope.resourceList = [
        {
            'displayName': 'Ambulance',
            'value': 'ambulance'
        },
        {
            'displayName': 'Hospital Beds',
            'value': 'hospital_bed'
        },
        {
            'displayName': 'ICU Beds',
            'value': 'hospital_bed_icu'
        },
        {
            'displayName': 'Oxygen',
            'value': 'oxygen'
        },
        {
            'displayName': 'Plasma',
            'value': 'plasma'
        }
    ];

    $scope.fetch = function (data) {
        url = api_base_url + "resource_type=" + data.resource.value + "&city=" + data.city + "&page_no=" + $scope.pageNumber;
        // url = 'api.txt';
        console.log("URL:  " + url);
        $scope.leads = "";
        $scope.hasMoreData = false;
        $scope.timeout = false;
        $http.get(url).then(function (response) {
            console.log(response.status);
            $scope.citySearched = data.city;
            $scope.resourceSearched = data.resource;
            if (response.status == 202) {
                if ($scope.retryCount > 0) {
                    $scope.keepLoading = true;
                    $timeout(function () { $scope.fetch(data) }, 5000);
                    $scope.retryCount--;
                }
                else{
                    $scope.waiting = false;
                    $scope.timeout = true;
                    $scope.dataFetched = true;
                }
            }
            else {
                $scope.leads = response.data.resource_info_data;
                $scope.hasMoreData = response.data.meta_info.more_data_available;
                $scope.dataFetched = true;
                console.log(response.data);
                $scope.waiting = false;
            }
            if ($scope.retryCount < 0) {
                $scope.waiting = false;
                $scope.dataFetched = true;
            }
            // console.log($scope.leads.data);
            // console.log("Hello");
        },
            function myError(response) {
                $scope.waiting = false;
                $scope.error = true;
                $scope.errMessage = response.data;
                // $scope.dataFetched = true;
            });
    };

    $scope.delayedFunction = function () {
        console.log("Hi I am delayed fun");
    };

    $scope.getFromNowDate = function (date) {
        var now = moment(date).fromNow();
        return now;
    };

    $scope.getDate = function (date) {
        var date = moment(date);
        return date.format('YYYY-MM-DD') + ' at ' + date.format('HH:mm');
    };


    $scope.fetchNextBatch = function (data) {
        $scope.waiting = true;
        $scope.pageNumber += 1;
        $scope.fetch($scope.filter);
    };

    $scope.fetchPreviousBatch = function (data) {
        $scope.waiting = true;
        $scope.pageNumber -= 1;
        $scope.fetch($scope.filter);
    };

    $scope.reset = function () {
        $scope.filter = angular.copy($scope.master);
        $scope.pageNumber = 1;
        $scope.retryCount = 2;
        // $scope.fetch($scope.master);
        $scope.leads = "";
        $scope.hasMoreData = false;
    };
    $scope.reset();

    $scope.submit = function () {
        $scope.init();
        $scope.waiting = true;
        $scope.error = false;
        // $scope.pageNumber = 0;
        $scope.fetchNextBatch($scope.filter);
    };
    $scope.init();
});

