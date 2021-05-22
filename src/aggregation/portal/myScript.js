var app = angular.module('myApp', []);
app.controller('formCtrl', function ($scope, $http, $timeout) {
    const api_base_url = "https://asia-south1-covisearch2.cloudfunctions.net/covisearchapi?";
    $scope.master = { city: "Mumbai", resource: "Oxygen" };
    
    $http.get('cities.txt').then(function (response) {
        $scope.cityList = response.data;
    });
    
    $scope.init = function () {
        $scope.pageNumber = 0;
        $scope.retryCount = 2;
        $scope.dataFetched = false;
    };

    $scope.resourceList = [
        "ambulance",
        "plasma",
        "hospital_bed",
        "hospital_bed_icu"
    ];

    $scope.bloodGroup = [
        { type: "ap" },
        { type: "an" },
        { type: "bp" },
        { type: "bn" }
    ];

    $scope.fetch = function (data) {
        url = api_base_url + "resource_type=" + data.resource + "&city=" + data.city + "&page_no=" + $scope.pageNumber;
        console.log("URL:  " + url);
        $scope.leads = "";
        $scope.hasMoreData = false;
        $http.get(url).then(function (response) {
            console.log(response.status);
            $scope.citySearched = data.city;
            $scope.resourceSearched = data.resource;
            if (response.status == 202) {
                if($scope.retryCount > 0)
                {
                    $scope.keepLoading = true;
                    $timeout(function () { $scope.fetch(data) }, 4000);
                    $scope.retryCount--;
                }
            }
            else{
                $scope.leads = response.data.resource_info_data;
                $scope.hasMoreData = response.data.meta_info.more_data_available;
                $scope.dataFetched = true;
                console.log(response.data);
                $scope.waiting = false;
            }
            if ($scope.retryCount == 0) {
                $scope.waiting = false;
                $scope.dataFetched = true;
            }
            // console.log($scope.leads.data);
            console.log("Hello");
        });
    };

    $scope.delayedFunction = function () {
        console.log("Hi I am delayed fun");
    };

    $scope.getFromNowDate = function (date) {
        var now = moment(date).fromNow();
        return now;
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
        // $scope.pageNumber = 0;
        $scope.fetchNextBatch($scope.filter);
    };
    $scope.init();
});

