$(document).ready(function () {
            $(".query").click(function () {
                var procedure_id = this.id

                $.post(
                    "procedureinfos",
                    JSON.stringify({
                        procedure_id: procedure_id,
                    }),
                    function (data) {
                        $('#mymodal').modal("show")
                        $("#procedure_id").text(data.id)
                        $("#user_name").text(data.user_name)
                        $("#user_name2").text(data.user_name)
                        $("#tel").text(data.tel)
                        $("#department").text(data.department)
                        $("#car_name").text(data.car_name)
                        $("#approval_time").text(data.approval_time)
                        $("#arrival_place").text(data.arrival_place)
                        $("#book_start_datetime").text(data.book_start_datetime)
                        $("#book_end_datetime").text(data.book_end_datetime)
                        $("#actual_start_datetime").text(data.actual_start_datetime)
                        $("#actual_end_datetime").text(data.actual_end_datetime)
                        $("#number").text(data.number)
                        $("#namelist").text(data.namelist)
                        $("#reason").text(data.reason)
                        $("#etc").text(data.etc)
                        $("#first_approval").text(data.first_approval)
                        $("#status1").text(data.status1)
                        $("#second_approval").text(data.second_approval)
                        $("#status2").text(data.status2)
                        $("#rejectreason").text(data.rejectreason)
                        $("#driver").text(data.driver)
                    }
                )
            })
        });