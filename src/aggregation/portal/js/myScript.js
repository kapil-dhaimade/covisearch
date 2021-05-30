var app = angular.module('myApp', []);
app.controller('formCtrl', function ($scope, $http, $timeout, $window) {
    const api_base_url = "https://asia-south1-covisearch2.cloudfunctions.net/covisearchapi?";
    var list = null;
    $scope.master = {
        city: "Delhi",
        resource: {
            'displayName': 'Oxygen',
            'value': 'oxygen',
            'image': 'images/icons/oxygen.png'
        }
    };
    $scope.screenStatus = 'loading';
    $http.get('../data/cities.txt').then(function (response) {
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
            'value': 'ambulance',
            'image': 'images/icons/ambulance.png'
        },
        {
            'displayName': 'Hospital Beds',
            'value': 'hospital_bed',
            'image': 'images/icons/hospital_bed.png'
        },
        {
            'displayName': 'ICU Beds',
            'value': 'hospital_bed_icu',
            'image': 'images/icons/icu.png'
        },
        {
            'displayName': 'Oxygen',
            'value': 'oxygen',
            'image': 'images/icons/oxygen.png'
        },
        {
            'displayName': 'Plasma',
            'value': 'plasma',
            'image': 'images/icons/plasma.png'
        }
    ];

    $scope.fetch = function (data) {
        url = api_base_url + "resource_type=" + data.resource.value + "&city=" + data.city + "&page_no=" + $scope.pageNumber;
        $scope.leads = "";
        $scope.hasMoreData = false;
        $http.get(url).then(function (response) {
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

    $scope.onPageLoad = function () {
        $scope.init();
        $scope.screenStatus = 'loading';
        $scope.fetchNextBatch($scope.master);
    }

    $scope.init();
    $scope.onPageLoad();
});

