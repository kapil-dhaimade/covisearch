var app = angular.module('myApp', []);
app.controller('formCtrl', function ($scope, $http, $timeout,$window) {
    const api_base_url = "https://asia-south1-covisearch2.cloudfunctions.net/covisearchapi?";
    var list = null;
    $scope.master = {
        city: "Delhi",
        resource: {
            'displayName': 'Oxygen',
            'value': 'oxygen'
        }
    };
    $scope.screenStatus = 'loading';
    $http.get('../data/cities.txt').then(function (response) {
        // $scope.cityList = response.data;
        list = response.data;
    });

    $scope.init = function () {
        $scope.pageNumber = 0;
        $scope.retryCount = 5;
        // $scope.screenStatus = 'home';
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
        console.log("URL:  " + url);
        $scope.leads = "";
        $scope.hasMoreData = false;
        $http.get(url).then(function (response) {
            console.log(response.status);
            $scope.citySearched = data.city;
            $scope.resourceSearched = data.resource;
            if (response.status == 202) {
                if ($scope.retryCount > 0) {
                    $timeout(function () { $scope.fetch(data) }, 2000);
                    $scope.retryCount--;
                    $scope.screenStatus = 'fetchingData';
                    return;
                }
                else {
                    $scope.screenStatus = "timeout";
                    return;
                }
            }
            else {
                $scope.leads = response.data.resource_info_data;
                $scope.hasMoreData = response.data.meta_info.more_data_available;
                console.log(response.data);
                $scope.screenStatus = 'dataFetched';
                $window.scrollTo(0, 0);
                return
            }
        },
            function myError(response) {
                $scope.errMessage = response.data;
                $scope.screenStatus = 'error';
            });
    };

    $scope.getFromNowDate = function (date) {
        var now = moment(date).fromNow();
        return now;
    };

    $scope.getDate = function (date) {
        var date = moment(date);
        return date.format('DD-MM-YYYY') + ' ' + date.format('hh:mm A');
    };


    $scope.fetchNextBatch = function (data) {
        if ($scope.hasMoreData == true || $scope.pageNumber == 0) {
            $scope.pageNumber += 1;
            $scope.screenStatus = 'loading';
            $scope.fetch($scope.master);
        }
    };

    $scope.fetchPreviousBatch = function (data) {
        if ($scope.pageNumber > 1) {
            $scope.pageNumber -= 1;
            $scope.screenStatus = 'loading';
            $scope.fetch($scope.master);
        }
    };

    $scope.reset = function () {
        $scope.filter = angular.copy($scope.master);
        // $scope.pageNumber = 1;
        // $scope.retryCount = 2;
        // $scope.screenStatus='loading';
        // $scope.fetch($scope.master);
        // $scope.leads = "";
        // $scope.hasMoreData = false;
    };
    $scope.reset();

    $scope.submit = function () {

        $scope.init();
        $scope.screenStatus = 'loading';
        $scope.master = angular.copy($scope.filter);
        $scope.fetchNextBatch($scope.master);
    };

    $scope.filterFunction = function () {
        if ($scope.filter.city) {
            var filter = $scope.filter.city.toLowerCase();
            var filterList = list.filter((country) => country.startsWith(filter));
            $scope.cityList = filterList.slice(0, 3);
        }
    };
    $scope.init();
    $scope.submit();
});

