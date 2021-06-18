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

    $http.get('../data/cities.json').then(function (response) {
        cityLocationData = response.data;
    });

    $scope.init = function () {
        $scope.pageNumber = 0;
        $scope.retryCount = 5;
        // $scope.screenStatus = 'home';
    };
    
    $scope.resourceList = getResourceList();

    $scope.fetch = function (data) {
        resource = getResource(data);
        url = api_base_url + "resource_type=" + resource.value + "&city=" + data.city +
                         "&page_no=" + $scope.pageNumber;
        // url = '../data/api.txt'
        $scope.leads = "";
        $scope.hasMoreData = false;
        $http.get(url).then(function (response) {
            $scope.citySearched = data.city;
            $scope.resourceSearched = resource;
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
        var now;
        if (date && date.trim()) {
            now = moment(date).fromNow();
        }
        else {
            now = "Not Specified"
        }
        return now;
    };

    $scope.getDate = function (date) {
        var date = moment(date);
        return date.format('DD-MM-YYYY');
    };

    $scope.getNumbers = function (number) {
        var contvertedNum;
        if (number != null && number >= 0) {
            contvertedNum = number;
        }
        else {
            contvertedNum = "N.A."
        }
        return contvertedNum;
    }

    $scope.checkIfHospitalBedICU = function (x) {
        if (x.available_no_ventilator_beds != null
            || x.available_ventilator_beds != null
            || x.total_available_icu_beds != null) {
            return true;
        }
        return false;
    }

    $scope.checkIfHospitalBed = function (x) {
        if (x.available_no_oxygen_beds != null
            || x.available_oxygen_beds != null
            || x.total_available_beds != null
            || x.available_covid_beds != null) {
            return true;
        }
        return false;
    }

    $scope.fetchNextBatch = function () {
        if ($scope.hasMoreData == true || $scope.pageNumber == 0) {
            $scope.pageNumber += 1;
            $scope.screenStatus = 'loading';
            $scope.fetch($scope.master);
        }
    };

    $scope.fetchPreviousBatch = function () {
        if ($scope.pageNumber > 1) {
            $scope.pageNumber -= 1;
            $scope.screenStatus = 'loading';
            $scope.fetch($scope.master);
        }
    };
    function waitForCityLocationDataAndSetNearbyCity(){
        if(typeof cityLocationData !== "undefined"){
            $scope.nearbycity = setNearbyCity($scope.master.city);
        }
        else{
            setTimeout(waitForCityLocationDataAndSetNearbyCity, 250);
        }
    }
    $scope.submitCity = function (city) {
        if($scope.filter !== undefined)
        {
            $scope.filter.city = city;
        }
        else
        {
            $scope["filter"] = {}
            $scope.filter["city"] = city;
            $scope.filter["resource"] = {
            'displayName': 'Oxygen',
            'value': 'oxygen',
            'image': 'images/icons/oxygen.png'};
        }
        $timeout(function() {
            angular.element('#submit-button').triggerHandler('click');
        });
    };
    
    $scope.submit = function () {
        $scope.init();
        $scope.screenStatus = 'loading';
        $scope.master = angular.copy($scope.filter);
        $scope.fetchNextBatch();
        waitForCityLocationDataAndSetNearbyCity()
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
        $scope.fetchNextBatch();
        waitForCityLocationDataAndSetNearbyCity()
    }

    $scope.copy = function (x) {
        const el = document.createElement('textarea');
        var str = copyingData($scope.master,x);
        el.value = str;
        document.body.appendChild(el);
        el.select();
        document.execCommand('copy');
        document.body.removeChild(el);
    };

    $scope.share = function (x) {
        var str = sharingData($scope.master,x);
        window.location.href = "whatsapp://send?text=" + encodeURIComponent(str);
    };

    $scope.init();
    $scope.onPageLoad();
});

