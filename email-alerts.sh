# Configure the variables from_email, password, to_email before running the script
# Run this on the machine not on containers
# Make sure you give execution permission to this file
# Keep this running in background by "./email-alerts.sh &"
# send-email.py is from Gist: https://gist.github.com/L-fours-gists/3837637 Thank you!

from_email='fromemail@gmail.com'
password='gmailpassword'
to_email='Your to name <toemail@gmail.com>'

(docker events  --filter 'event=die' &) | while read event
do 
    container_name=$(echo "$event" | awk '{print $17}')
    container_id=$(echo "$event" | awk '{print $4}')
    exit_time=$(echo "$event" | awk '{print $1}')
    logs="$(docker logs -t $container_id  2>&1 )"
    python send-email.py \
        --user "$from_email" \
        --pass "$password" \
        --to "$to_email" \
        --subject "Container with $container_name exited at $exit_time" \
        --body "$logs"
done