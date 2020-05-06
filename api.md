# API Document

## `/analysis`

### Description
Send full image and return multiple face bbox, emotions, age and gender

### Method
POST

### Parameters
* `img`: a list of str, base64 string of images

### Returns
* `result`: a list of dict, faces results
  * `bbox_x`: a int, face bbox x absolute coordinate (not ratio)
  * `bbox_y`: a int, face bbox y absolute coordinate (not ratio)
  * `bbox_w`: a int, face bbox w absolute value (not ratio)
  * `bbox_h`: a int, face bbox h absolute value (not ratio)
  * `age`: a int, face age estimation
  * `gender`: a str, face gender estimation `F` or `M`
  * `emotion`: a list of dict, face emotion estimation sorted by score
    * `category`: a str, emotion string, e.g., `Happy`, `Fear`, `Sad`
    * `score`: a float, emotion score
* `trx_id`: a str, request uuid
* `time_cost`: a float, total run time of deep face

### Errors
* HTTP 205 Reset Content
```python
{
  "success": False, 
  "error": "you must pass at least one img object in your request"
}
```
