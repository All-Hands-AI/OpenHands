img_name_partial="<mnone>" # Our images don't currently have a name.
found="$(docker images | (grep "$img_name_partial" | head -1))"

if [ -n "$found" ]; then
  export SANDBOX_RUNTIME_CONTAINER_IMAGE=$(echo $found | awk '{print $3}' || :)
  echo -e "✅ Selected image:\n$found"
else
  echo -e "❌ ERROR: IMAGE not found. Here are all images:"
  docker image list --all
fi
