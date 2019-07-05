$(document).ready(function(){
/*
	$("#im").mousemove(function(e){
		if(!this.canvas){
			this.canvas = $("<canvas>")[0];
			this.canvas.width = this.width;
			this.canvas.height = this.height;

			alert(this.canvas.width);
			alert(this.canvas.height);

			this.canvas.getContext("2d").drawImage(this, 0, 0, this.width, this.height);
		}

		var pixel = this.canvas.getContext("2d").getImageData(e.offsetX, e.offsetY, 1, 1).data;
	});
*/

	function foo(){
		var file_data = new FormData($("#file_form")[0]);
		$.ajax({
			type: "POST",
			url: "process",
			data: file_data,
			processData : false,
			contentType: false,
			success: function(x){
				if(x != "Failed to create mosaic.") {
					var l = x.split(",");
					$("#photo").attr("src", "tmp/hot_" + l.slice(-3, -2)).css("display", "inline");
					$("#hist").attr("src", "tmp/hist_" + l.slice(-3, -2)).css("display", "inline");
					$("#colorscale").css("display", "inline");
					$("#legend_left").html(l.slice(-2, -1) + "&nbsp;");
					$("#legend_right").html(l.slice(-1));
					$("#bar").text("");
				} else {
					$("#photo").css("display", "none");
					$("#hist").css("display", "none");
					$("#colorscale").css("display", "none");
					$("#legend_left").html("");
					$("#legend_right").html("");
					$("#bar").text(x);
				}
				/*
				var ctx = document.getElementById("palette").getContext("2d");
				var grad = ctx.createLinearGradient(0, 0, 640, 0);
				grad.addColorStop(0, "black");
				grad.addColorStop(1, "white");

				ctx.fillStyle = grad;
				ctx.fillRect(0, 0, 640, 100);
				*/
			}
		});
	}

	$("#file_form input[type=file]").change(function(){
		foo();
	});

	$("#temp_form input[type=number]").change(function(){
		var max_data = $("#id_max_field").val()
		var min_data = $("#id_min_field").val()
		$.ajax({
			type: "POST",
			url: "temp",
			data: {
				'max_field' : max_data,
				'min_field' : min_data
			},
			success: function(){
				foo();
			}
		});
	});

	$("#photo").click(function(e){
		var offset = $(this).offset();

		var coord_x = (e.pageX - offset.left);
		var coord_y = (e.pageY - offset.top);

		$.get(
			"raw",
			{
				x: coord_x,
				y: coord_y
			}
		).done(function(x){
			$("#bar").html(x);
		});
	});

});
