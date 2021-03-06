<?php
/**
* Created by PhpStorm.
* User: shira
* Date: 17/02/2019
* Time: 16:28
*/
?>

<!doctype html>
<html lang="en">
<head>
    <!-- Required meta tags -->
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">

    <!--&lt;!&ndash; Bootstrap CSS &ndash;&gt;-->
    <link rel="stylesheet" href="../TranslateProject/css/bootstrap.min.css">
    <link rel="stylesheet" href="../TranslateProject/css/bootstrap.min.css">


    <link href="//maxcdn.bootstrapcdn.com/bootstrap/3.3.0/css/bootstrap.min.css" rel="stylesheet" id="bootstrap-css">
    <script src="//maxcdn.bootstrapcdn.com/bootstrap/3.3.0/js/bootstrap.min.js"></script>
    <script src="//code.jquery.com/jquery-1.11.1.min.js"></script>
    <!------ Include the above in your HEAD tag ---------->

    <link href="https://fonts.googleapis.com/css?family=Oleo+Script:400,700" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css?family=Teko:400,700" rel="stylesheet">
    <link href="https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css" rel="stylesheet">

    <title>Converter</title>
</head>

<body>
<style>
    body {
        background-image: url("background2.png");
        background-position: center;
        background-repeat: no-repeat;
        background-size: cover;
        height: 650px;
    }

</style>
<!-- Page Content -->
<div class="container">
    <div class="row">
        <div class="col-lg-12 text-center">
            <h1 class="mt-10"><b>SQL to MONGO Converter</b></h1>
            <p class="lead"> </p>
        </div>
    </div>
</div>

<section id="contact">
    <div class="section-content text-center">
        <h1 class="section-header"> <span class="content-header wow fadeIn " data-wow-delay="0.2s" data-wow-duration="2s"> Translate</span> your query</h1>
        <h3>Write your query and click <b>TRANSLATE</b></h3>
    </div>
    <div class="contact-section">
        <div class="container">
            <form action="Converter.php" method="post">
                <div class="col-md-6 form-line">
                    <div class="form-group">
                        <label> From </label>
                    </div>
                    <div class="form-group">
                        <?php
                            if( isset( $_POST['submit'])){
                                $QueryString = $_POST['QueryString'];
                                $QueryString = str_replace("\n", " ", $QueryString);
                                $QueryString = str_replace('"', "'",$QueryString);
                                $QueryString = str_replace("<>", "NEQ", $QueryString);
                                $QueryString = str_replace(">=", "GEQ", $QueryString);
                                $QueryString = str_replace("<=", "LEQ", $QueryString);
                                $QueryString = str_replace("!<", "GTR", $QueryString);
                                $QueryString = str_replace("!>", "LSS", $QueryString);
                                $QueryString = str_replace("<", "LSS", $QueryString);
                                $QueryString = str_replace(">", "GTR", $QueryString);
                                $JsonString = exec("python SQL_to_JSON.py $QueryString");
                                $temp = str_replace("@", "\n", $JsonString);
                                $result = explode("`", $temp);
                                echo "<textarea  type=\"text\" class=\"form-control input-group-lg\" id=\"original\" name=\"QueryString\" rows=\"5\" cols=\"10\">$QueryString</textarea>";
                                }
                            else {
                                echo "<textarea  type=\"text\" class=\"form-control input-group-lg\" id=\"original\" name=\"QueryString\" rows=\"5\" cols=\"10\" placeholder=\"Enter Your Text\"></textarea>";
                            }
                            ?>
                    </div>
                </div>

                <div class="col-md-6 form-line">
                    <div class="form-group">
                        <label> To </label>
                    </div>
                    <div class="form-group">
                        <?php
                        if( isset( $_POST['submit'])){
                            echo " <textarea type='text'  class=\"form-control input-group-lg\" id=\"middle\" name=\"MongoString\" rows=\"5\" cols=\"10\" >$result[0]</textarea>";
                        }
                        else {
                            echo " <textarea type='text'  class=\"form-control input-group-lg\" id=\"middle\" name=\"MongoString\" rows=\"5\" cols=\"10\" placeholder=\"Translated text will be here\"></textarea>";
                        }
                        ?>
                    </div>
                </div>

                <div class="col-md-12">
                    <div class="form-group">
                        <label> Result </label>
                    </div>
                    <div class="form-group">
                        <?php
                            if( isset( $_POST['submit'])){
                                echo " <textarea type='text'  class=\"form-control input-group-lg\" id=\"translated\" name=\"JsonString\" rows=\"10\" cols=\"10\" >$result[1]</textarea>";
                            }
                            else {
                                echo " <textarea type='text'  class=\"form-control input-group-lg\" id=\"translated\" name=\"JsonString\" rows=\"10\" cols=\"10\" placeholder=\"Translated text will be here\"></textarea>";
                            }
                        ?>

                    </div>
                    <div>
                        <button type="submit"name="submit" class="btn btn-block submit"><i class="fa fa-globe" aria-hidden="true"></i>Translate</button>
                    </div>

                </div>
            </form>
        </div></div>
</section>

<!-- Bootstrap core JavaScript -->
<script src="../TranslateProject/js/jquery.min.js"></script>
<script src="../TranslateProject/js/bootstrap.bundle.min.js"></script>

</body>
</html>
