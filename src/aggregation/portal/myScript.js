var app = angular.module('myApp', []);
app.controller('formCtrl', function($scope,$http) {
    const api_base_url ="https://api.covidcitizens.org/api/v1/leadbyquery?";
    $scope.dataFetched=false;
    // $scope.master = {city:{city:"Mumbai"}, resource:"Plasma"};
    $scope.cityList = [
        "Mumbai",
        "Delhi",
        "Banglore",
        "Pune",
        "Lucknow",
        "Surat"
    ];

    $scope.resourceList = [
        "Ambulance",
        "Plasma",
        "Hospital",
         "Oxygen"
    ];

    $scope.bloodGroup = [
        {type : "ap"},
        {type : "an"},
        {type : "bp"},
        {type : "bn"}
    ];

    // $scope.dataFormat=
    // [
    //     "location","contact_type","category","uuid","source","name","phone","lastverified"
    // ]

    $scope.fetch = function(data){
        url = api_base_url+"category="+data.resource+"&location="+data.city;
        console.log("URL:  "+ url);
        $http.get(url).then(function (response) {
            $scope.leads = response.data;
            console.log(response.data);
            console.log($scope.leads.data);
        });
        $scope.dataFetched=true;
        var now =moment("2021-05-17#10:26:08.937881-06:00").fromNow();
        $scope.date= now;
        var str ='12345,23456,34,567';
        $scope.numbers = str;
    }
    
    $scope.reset = function() {
        $scope.filter = angular.copy($scope.master);
        // $scope.fetch($scope.master);
        $scope.dataFetched=false;
        $scope.leads = "";
    };
    // $scope.reset();



    $scope.submit = function() {
        $scope.fetch($scope.filter);
    };
});

