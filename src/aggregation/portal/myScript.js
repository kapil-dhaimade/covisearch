var app = angular.module('myApp', []);
app.controller('formCtrl', function ($scope, $http, $timeout) {
    const api_base_url = "https://api.covidcitizens.org/api/v1/leadbyquery?";
    $scope.dataFetched = false;
    $scope.master = { city: "Pune", resource: "Ambulance" };
    $scope.pageNumber = 0;
    $scope.moreData = true;
    $http.get('cities.txt').then(function (response) {
        $scope.cityList = response.data;
    });

    $scope.resourceList = [
        "Ambulance",
        "Plasma",
        "Hospital",
        "Oxygen"
    ];

    $scope.bloodGroup = [
        { type: "ap" },
        { type: "an" },
        { type: "bp" },
        { type: "bn" }
    ];

    // $scope.dataFormat=
    // [
    //     "location","contact_type","category","uuid","source","name","phone","lastverified"
    // ]

    $scope.fetch = function (data) {
        url = api_base_url + "category=" + data.resource + "&location=" + data.city + "&page=" + $scope.pageNumber;
        console.log("URL:  " + url);
        $scope.waiting = true;
        $http.get(url).then(function (response) {
            $scope.leads = response.data;
            console.log(response.data);
            console.log($scope.leads.data);
            console.log(response.status);
            if (response.status == 203) {
                $scope.keepLoading = true;
                $timeout(function () { $scope.fetchNextBatch(data) }, 4000);
            }
            console.log("Hello");
        });

        $scope.dataFetched = true;
        $scope.waiting = false;
        var now = moment("2021-05-17#10:26:08.937881-06:00").fromNow();
        $scope.date = now;
        var str = '12345,23456,34,567';
        $scope.numbers = str;
    }

    $scope.delayedFunction = function () {
        console.log("Hi I am delayed fun");
    }
    $scope.fetchNextBatch = function (data) {
        $scope.pageNumber += 1;
        $scope.fetch($scope.filter);
    }

    $scope.fetchPreviousBatch = function (data) {
        $scope.pageNumber -= 1;
        $scope.fetch($scope.filter);
    }

    $scope.reset = function () {
        $scope.filter = angular.copy($scope.master);
        $scope.fetch($scope.master);
        $scope.dataFetched = false;
        $scope.leads = "";
    };
    $scope.reset();

    $scope.submit = function () {
        $scope.waiting = true;
        $scope.pageNumber = 0;
        $scope.fetchNextBatch($scope.filter);
    };
});

