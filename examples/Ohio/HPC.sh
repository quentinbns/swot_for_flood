#!/bin/bash
#SBATCH -N 1
#SBATCH -p prod
# #SBATCH -o ACP_SWOT.out
# #SBATCH -e ACP_SWOT.err
# #SBATCH -J ACP_SWOT
# #SBATCH --ntasks-per-node=1

#SBATCH -o pretreat_pixc.out
#SBATCH -e pretreat_pixc.err
#SBATCH -J pretreat_pixc
#SBATCH --ntasks-per-node=12
#SBATCH  --dependency=48158


# >>> conda initialize >>>
# !! Contents within this block are managed by 'conda init' !!
__conda_setup="$('/data/softs/anaconda3-2020.07/bin/conda' 'shell.bash' 'hook' 2> /dev/null)"
if [ $? -eq 0 ]; then
    eval "$__conda_setup"
else
    if [ -f "/data/softs/anaconda3-2020.07/etc/profile.d/conda.sh" ]; then
        . "/data/softs/anaconda3-2020.07/etc/profile.d/conda.sh"
    else
        export PATH="/data/softs/anaconda3-2020.07/bin:$PATH"
    fi
fi

unset __conda_setup
conda deactivate
# <<< conda initialize <<< 
conda activate conda3.10

# print python version
echo "Python version:"
python --version

# print conda version
echo "Conda version:"
conda --version

python3 pretreat.py