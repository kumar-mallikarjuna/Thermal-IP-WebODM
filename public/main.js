$(document).ready(function(){
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

		$("#bar").html("R: " + pixel[0]);
	});


	$("#file_form input[type=file]").change(function(){
		var file_data = new FormData($("#file_form")[0]);
		$.ajax({
			type: "POST",
			url: "process",
			data: file_data,
			processData : false,
			contentType: false,
			success: function(x){
				$("#photo").attr("src", "tmp/temperature_" + x).css("display", "block");
				var ctx = document.getElementById("palette").getContext("2d");
				var grad = ctx.createLinearGradient(0,0, 640, 0);
				grad.addColorStop(0, "black");
				grad.addColorStop(1, "white");

				ctx.fillStyle = grad;
				ctx.fillRect(0, 0, 640, 100);
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
