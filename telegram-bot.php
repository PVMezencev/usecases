<?php
include('autoload.php'); //Подключаем библиотеку

use \unreal4u\TelegramAPI\HttpClientRequestHandler;
use \unreal4u\TelegramAPI\TgLog;
use \unreal4u\TelegramAPI\Telegram\Methods\SendPhoto;
use \unreal4u\TelegramAPI\Telegram\Methods\SendMessage;
use \unreal4u\TelegramAPI\Telegram\Methods\SendMediaGroup;
use \unreal4u\TelegramAPI\Telegram\Types\Message;
use \unreal4u\TelegramAPI\Telegram\Types\Custom\InputFile;
use \unreal4u\TelegramAPI\Telegram\Types\InputMedia\Photo;

$tasks_dir = 'tg_task';

if (isset($_GET['req_type']) && $_GET['req_type'] == 'cron') {
    
    
    $tasks = scandir($tasks_dir.'/');
    $tasks = array_diff($tasks , array('..', '.'));
    
    foreach ($tasks as $task) {
        $task_fn = $tasks_dir.'/'.$task;
        $file = fopen($task_fn,'r');
        $json = fread($file, filesize($task_fn));
        fclose($file);
        $post = json_decode($json);
        $botKey = '$botKey';
        
        $chatId = '$chatId';
        $attachments = $post->{'attachments'};
        
        $img_urls = [];
        $video_urls = [];
        
        foreach ($attachments as $attach) {
            if ($attach->type == 'photo') {
                $photo = $attach->photo;
                $sizes = $photo->sizes;
                $key = $photo->id;
                if (!is_array($sizes) || count($sizes) === 0) continue;
            
                $size = array_pop($sizes);
                $img_url = $size->url;
                $img_name = $key . '.jpg';
                array_push($img_urls, $img_url);
            } else if ($attach->type == 'video') {
                $video = $attach->video;
                $width = $video->width;
                try {
                    $_video = get_object_vars($video);
                    $img_url = $_video['photo_1280'];
                    array_push($img_urls, $img_url);
                    $img_url = $_video['first_frame_1280'];
                    array_push($img_urls, $img_url);
                } catch (Exception $e) {
                    
                }
            }
        }
        
        $loop = \React\EventLoop\Factory::create();
        $handler = new HttpClientRequestHandler($loop);
        $tgLog = new TgLog($botKey, $handler);
        
        $messageText = $post->{'text'};
         if (count($img_urls) > 1) {
            
        
            $sendMessage = new SendMessage();
            $sendMessage->chat_id = $chatId;
            $sendMessage->text = $messageText;
            
            $firstMessagePromise = $tgLog->performApiRequest($sendMessage);
            $loop->run();
        
            $firstMessagePromise->then(
                static function (Message $sendedMsg) use ($tgLog, $img_urls, $chatId) {
                    
                    $sendMediaGroup = new SendMediaGroup();
                    
                    try {
                        foreach ($img_urls as $_img) {
                            $inputMediaPhoto = new Photo();
                            $inputMediaPhoto->media = $_img;
                            $sendMediaGroup->media[] = $inputMediaPhoto;
                        }
                        $sendMediaGroup->chat_id = $chatId;
                        $message_id = $sendedMsg->message_id;
                        $sendMediaGroup->reply_to_message_id = $message_id;
                        $promise = $tgLog->performApiRequest($sendMediaGroup);
                    } catch (Exception $e) {// Onoes, an exception occurred...
                            echo 'Exception ' . get_class($exception) . ' $sendMediaGroup, message: ' . $exception->getMessage() . PHP_EOL;
                            return;
                    }
        
                    $promise->then(
                        static function ($response) {
                            echo('ok');
                        },
                        static function (\Exception $exception) {
                            // Onoes, an exception occurred...
                            echo 'Exception ' . get_class($exception) . ' $promise->then, message: ' . $exception->getMessage() . PHP_EOL;
                            return;
                        }
                    );
                },
        
                static function (\Exception $exception) {
                    // Onoes, an exception occurred...
                    echo 'Exception ' . get_class($exception) . ' $firstMessagePromise->then, message: ' . $exception->getMessage() . PHP_EOL;
                    return;
                }
            );
        
        
            $loop->run();
            
        
        } else if (count($img_urls) == 1) {
            if ((strlen($messageText) > 1024)) {
                // Caption для фото не принимает текст более 1024 символов, по этому отправиом по одному.
                $sendMessage = new SendMessage();
                $sendMessage->chat_id = $chatId;
                $sendMessage->text = $messageText;
                
                $firstMessagePromise = $tgLog->performApiRequest($sendMessage);
                $loop->run();
                
                $firstMessagePromise->then(
                    static function (Message $sendedMsg) use ($tgLog, $img_urls, $chatId) {
                
                        $sendPhoto = new SendPhoto();
                        $sendPhoto->chat_id = $chatId;
                        $sendPhoto->photo = $img_urls[0];
                        $message_id = $sendedMsg->message_id;
                        $sendPhoto->reply_to_message_id = $message_id;
                        $promise = $tgLog->performApiRequest($sendPhoto);
                        
                        $promise->then(
                            static function ($response) {
                                echo('ok');
                            },
                            static function (\Exception $exception) {
                                // Onoes, an exception occurred...
                                echo 'Exception ' . get_class($exception) . ' $promise->then, message: ' . $exception->getMessage() . PHP_EOL;
                                return;
                            }
                        );
                    },
            
                    static function (\Exception $exception) {
                        // Onoes, an exception occurred...
                        echo 'Exception ' . get_class($exception) . ' $firstMessagePromise->then, message: ' . $exception->getMessage() . PHP_EOL;
                        return;
                    }
                );
                
        
                $loop->run();
                
            } else {
        
                $sendPhoto = new SendPhoto();
                $sendPhoto->chat_id = $chatId;
                $sendPhoto->photo = $img_urls[0];
                $sendPhoto->caption = $messageText;
            
                $promise = $tgLog->performApiRequest($sendPhoto);
            
                $promise->then(
                    function ($response) {
                        echo('ok');
                    },
                    function (\Exception $exception) {
                        // Onoes, an exception occurred...
                        echo 'Exception ' . get_class($exception) . ' caught, message: ' . $exception->getMessage();
                        return;
                    }
                );
            
                $loop->run();
            }
        
        
        } else {
        
            $sendMessage = new SendMessage();
            $sendMessage->chat_id = $chatId;
            $sendMessage->text = $messageText;
            
            $promise = $tgLog->performApiRequest($sendMessage);
            $promise->then(
                static function ($response) {
                    echo('ok');
                },
                static function (\Exception $exception) {
                    // Onoes, an exception occurred...
                    echo 'Exception ' . get_class($exception) . ' caught, message: ' . $exception->getMessage() . PHP_EOL;
                    return;
                }
            );
            $loop->run();
        
        }
        unlink($task_fn);
    }
    
    return;
}

// Получить данные POST запроса.
$postData = file_get_contents('php://input');
$data = json_decode($postData, false);

if (!$data) return;

if ($data->type === 'confirmation' && $data->group_id === group_id) {
    echo 'echo';
    return;
}
if ($data->secret !== 'secret') return;
if ($data->type !== 'wall_post_new') return;

$post = $data->object;
$post_id = $post->id;

$post_json = json_encode($data->object, JSON_HEX_TAG | JSON_HEX_APOS | JSON_HEX_QUOT | JSON_HEX_AMP | JSON_UNESCAPED_UNICODE);

if (!file_exists($tasks_dir)) {
    mkdir($tasks_dir, 0777, true);
}
$file = fopen($tasks_dir.'/task_'.$post_id.'.json','w+');
fwrite($file, $post_json);
fclose($file);

echo('ok');
