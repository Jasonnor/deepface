import math
import warnings

from deepface.commons.functions import loadBase64Img

warnings.filterwarnings("ignore")
import time
import os
import numpy as np
from tqdm import tqdm
import json
import cv2

# from basemodels import VGGFace, OpenFace, Facenet, FbDeepFace
# from extendedmodels import Age, Gender, Race, Emotion
# from commons import functions, realtime, distance as dst

from deepface.basemodels import VGGFace, OpenFace, Facenet, FbDeepFace
from deepface.extendedmodels import Age, Gender, Race, Emotion
from deepface.commons import functions, realtime, distance as dst


def verify(img1_path, img2_path=''
           , model_name='VGG-Face', distance_metric='cosine', model=None):
    tic = time.time()

    if type(img1_path) == list:
        bulkProcess = True
        img_list = img1_path.copy()
    else:
        bulkProcess = False
        img_list = [[img1_path, img2_path]]

    # ------------------------------

    if model == None:
        if model_name == 'VGG-Face':
            print("Using VGG-Face model backend and", distance_metric, "distance.")
            model = VGGFace.loadModel()

        elif model_name == 'OpenFace':
            print("Using OpenFace model backend", distance_metric, "distance.")
            model = OpenFace.loadModel()

        elif model_name == 'Facenet':
            print("Using Facenet model backend", distance_metric, "distance.")
            model = Facenet.loadModel()

        elif model_name == 'DeepFace':
            print("Using FB DeepFace model backend", distance_metric, "distance.")
            model = FbDeepFace.loadModel()

        else:
            raise ValueError("Invalid model_name passed - ", model_name)
    else:  # model != None
        print("Already built model is passed")

    # ------------------------------
    # face recognition models have different size of inputs
    input_shape = model.layers[0].input_shape[1:3]

    # ------------------------------

    # tuned thresholds for model and metric pair
    threshold = functions.findThreshold(model_name, distance_metric)

    # ------------------------------
    resp_objects = []
    for instance in img_list:
        if type(instance) == list and len(instance) >= 2:
            img1_path = instance[0]
            img2_path = instance[1]

            # ----------------------
            # crop and align faces

            img1 = functions.detectFace(img1_path, input_shape)
            img2 = functions.detectFace(img2_path, input_shape)

            # ----------------------
            # find embeddings

            img1_representation = model.predict(img1)[0, :]
            img2_representation = model.predict(img2)[0, :]

            # ----------------------
            # find distances between embeddings

            if distance_metric == 'cosine':
                distance = dst.findCosineDistance(img1_representation, img2_representation)
            elif distance_metric == 'euclidean':
                distance = dst.findEuclideanDistance(img1_representation, img2_representation)
            elif distance_metric == 'euclidean_l2':
                distance = dst.findEuclideanDistance(dst.l2_normalize(img1_representation),
                                                     dst.l2_normalize(img2_representation))
            else:
                raise ValueError("Invalid distance_metric passed - ", distance_metric)

            # ----------------------
            # decision

            if distance <= threshold:
                identified = "true"
            else:
                identified = "false"

            # ----------------------
            # response object

            resp_obj = "{"
            resp_obj += "\"verified\": " + identified
            resp_obj += ", \"distance\": " + str(distance)
            resp_obj += ", \"max_threshold_to_verify\": " + str(threshold)
            resp_obj += ", \"model\": \"" + model_name + "\""
            resp_obj += ", \"similarity_metric\": \"" + distance_metric + "\""
            resp_obj += "}"

            resp_obj = json.loads(resp_obj)  # string to json

            if bulkProcess == True:
                resp_objects.append(resp_obj)
            else:
                # K.clear_session()
                return resp_obj
        # ----------------------

        else:
            raise ValueError("Invalid arguments passed to verify function: ", instance)

    # -------------------------

    toc = time.time()

    # print("identification lasts ",toc-tic," seconds")

    if bulkProcess == True:
        resp_obj = "{"

        for i in range(0, len(resp_objects)):
            resp_item = json.dumps(resp_objects[i])

            if i > 0:
                resp_obj += ", "

            resp_obj += "\"pair_" + str(i + 1) + "\": " + resp_item
        resp_obj += "}"
        resp_obj = json.loads(resp_obj)
        return resp_obj


# return resp_objects


def analyze(img_path, actions=[], models={}):
    if type(img_path) == list:
        img_paths = img_path.copy()
        bulkProcess = True
    else:
        img_paths = [img_path]
        bulkProcess = False

    # ---------------------------------

    # if a specific target is not passed, then find them all
    if len(actions) == 0:
        actions = ['emotion', 'age', 'gender', 'race']

    print("Actions to do: ", actions)

    # ---------------------------------

    if 'emotion' in actions:
        if 'emotion' in models:
            print("already built emotion model is passed")
            emotion_model = models['emotion']
        else:
            emotion_model = Emotion.loadModel()

    if 'age' in actions:
        if 'age' in models:
            print("already built age model is passed")
            age_model = models['age']
        else:
            age_model = Age.loadModel()

    if 'gender' in actions:
        if 'gender' in models:
            print("already built gender model is passed")
            gender_model = models['gender']
        else:
            gender_model = Gender.loadModel()

    if 'race' in actions:
        if 'race' in models:
            print("already built race model is passed")
            race_model = models['race']
        else:
            race_model = Race.loadModel()
    # ---------------------------------

    resp_objects = []
    for img_path in img_paths:

        resp_obj = "{"

        # TO-DO: do this in parallel

        pbar = tqdm(range(0, len(actions)), desc='Finding actions')

        action_idx = 0
        img_224 = None  # Set to prevent re-detection
        # for action in actions:
        for index in pbar:
            action = actions[index]
            pbar.set_description("Action: %s" % (action))

            if action_idx > 0:
                resp_obj += ", "

            if action == 'emotion':
                emotion_labels = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']
                img = functions.detectFace(img_path, (48, 48), True)

                emotion_predictions = emotion_model.predict(img)[0, :]

                sum_of_predictions = emotion_predictions.sum()

                emotion_obj = "\"emotion\": {"
                for i in range(0, len(emotion_labels)):
                    emotion_label = emotion_labels[i]
                    emotion_prediction = 100 * emotion_predictions[i] / sum_of_predictions

                    if i > 0: emotion_obj += ", "

                    emotion_obj += "\"%s\": %s" % (emotion_label, emotion_prediction)

                emotion_obj += "}"

                emotion_obj += ", \"dominant_emotion\": \"%s\"" % (emotion_labels[np.argmax(emotion_predictions)])

                resp_obj += emotion_obj

            elif action == 'age':
                if img_224 is None:
                    img_224 = functions.detectFace(img_path, (224, 224),
                                                   False)  # just emotion model expects grayscale images
                # print("age prediction")
                age_predictions = age_model.predict(img_224)[0, :]
                apparent_age = Age.findApparentAge(age_predictions)

                resp_obj += "\"age\": %s" % (apparent_age)

            elif action == 'gender':
                if img_224 is None:
                    img_224 = functions.detectFace(img_path, (224, 224),
                                                   False)  # just emotion model expects grayscale images
                # print("gender prediction")

                gender_prediction = gender_model.predict(img_224)[0, :]

                if np.argmax(gender_prediction) == 0:
                    gender = "Woman"
                elif np.argmax(gender_prediction) == 1:
                    gender = "Man"

                resp_obj += "\"gender\": \"%s\"" % (gender)

            elif action == 'race':
                if img_224 is None:
                    img_224 = functions.detectFace(img_path, (224, 224),
                                                   False)  # just emotion model expects grayscale images
                race_predictions = race_model.predict(img_224)[0, :]
                race_labels = ['asian', 'indian', 'black', 'white', 'middle eastern', 'latino hispanic']

                sum_of_predictions = race_predictions.sum()

                race_obj = "\"race\": {"
                for i in range(0, len(race_labels)):
                    race_label = race_labels[i]
                    race_prediction = 100 * race_predictions[i] / sum_of_predictions

                    if i > 0: race_obj += ", "

                    race_obj += "\"%s\": %s" % (race_label, race_prediction)

                race_obj += "}"
                race_obj += ", \"dominant_race\": \"%s\"" % (race_labels[np.argmax(race_predictions)])

                resp_obj += race_obj

            action_idx = action_idx + 1

        resp_obj += "}"

        resp_obj = json.loads(resp_obj)

        if bulkProcess == True:
            resp_objects.append(resp_obj)
        else:
            return resp_obj

    if bulkProcess == True:
        resp_obj = "{"

        for i in range(0, len(resp_objects)):
            resp_item = json.dumps(resp_objects[i])

            if i > 0:
                resp_obj += ", "

            resp_obj += "\"instance_" + str(i + 1) + "\": " + resp_item
        resp_obj += "}"
        resp_obj = json.loads(resp_obj)
        return resp_obj


# return resp_objects


def detectFace(img_path):
    img = functions.detectFace(img_path)[0]  # detectFace returns (1, 224, 224, 3)
    return img[:, :, ::-1]  # bgr to rgb


def stream(db_path, model_name='VGG-Face', distance_metric='cosine', enable_face_analysis=True):
    realtime.analysis(db_path, model_name, distance_metric, enable_face_analysis)


def analysis(img_input, models=None):
    # TODO: try to only load model once
    tic = time.time()

    if 'emotion' in models:
        emotion_model = models['emotion']
    else:
        emotion_model = Emotion.loadModel()

    if 'age' in models:
        age_model = models['age']
    else:
        age_model = Age.loadModel()

    if 'gender' in models:
        gender_model = models['gender']
    else:
        gender_model = Gender.loadModel()

    open_cv_path = functions.get_opencv_path()
    face_detector_path = open_cv_path + "haarcascade_frontalface_default.xml"
    face_cascade = cv2.CascadeClassifier(face_detector_path)
    print("Face detector model loaded")
    toc = time.time()
    print("Facial attribute analysis models loaded in ", toc - tic, " seconds")

    input_shape = (224, 224)
    # Results: a list of image list of face dict
    results = []
    if type(img_input) == list:
        images = img_input.copy()
    else:
        images = [img_input]
    for img in images:
        if len(img) > 11 and img[0:11] == "data:image/":
            img = loadBase64Img(img)
        elif type(img).__module__ != np.__name__:
            # Check if is file path
            if not os.path.isfile(img):
                raise ValueError("Confirm that ", img, " exists")
            img = cv2.imread(img)

        raw_img = img.copy()

        image_result = []
        face_bboxes = face_cascade.detectMultiScale(img, 1.3, 5)
        for (x, y, w, h) in face_bboxes:
            face_result = {
                'bbox_x': int(x),
                'bbox_y': int(y),
                'bbox_w': int(w),
                'bbox_h': int(h)
            }
            # crop face by bbox
            cropped_face = raw_img[y:y + h, x:x + w]

            # TODO: Maybe we don't need to detect twice?
            # emotion
            gray_img = functions.detectFace(cropped_face, (48, 48), True)
            emotion_labels = ['Angry', 'Disgust', 'Fear', 'Happy', 'Sad', 'Surprise', 'Neutral']
            emotion_predictions = emotion_model.predict(gray_img)[0, :]
            sum_of_predictions = emotion_predictions.sum()
            emotion_result = []
            for i, emotion_label in enumerate(emotion_labels):
                emotion_prediction = emotion_predictions[i] / sum_of_predictions
                emotion_result.append({
                    'category': emotion_label,
                    'score': float(emotion_prediction)
                })
            face_result['emotion'] = sorted(
                emotion_result, key=lambda k: k['score'], reverse=True)

            # TODO: Maybe we don't need to detect twice?
            # age
            face_224 = functions.detectFace(cropped_face, input_shape, False)
            age_predictions = age_model.predict(face_224)[0, :]
            apparent_age = Age.findApparentAge(age_predictions)
            face_result['age'] = math.floor(apparent_age)

            # gender
            gender_prediction = gender_model.predict(face_224)[0, :]
            if np.argmax(gender_prediction) == 0:
                gender = 'F'
            else:
                gender = 'M'
            face_result['gender'] = gender

            image_result.append(face_result)
        results.append(image_result)
    return results


# ---------------------------

functions.allocateMemory()

functions.initializeFolder()

# ---------------------------
