import click
import os
import concurrent.futures
from itertools import product, permutations, combinations
from tqdm import tqdm
import pandas as pd
from Bio import SeqIO
from pairwise_ncd import return_byte, compressed_size, compute_distance

from pathlib import Path

@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option("-f", "--fasta", type=click.Path(dir_okay=False, exists=True, resolve_path=True), multiple=True, help="FASTA file containing sequence to compare")
@click.option("-d", "--directory", "directories", type=click.Path(dir_okay=True, file_okay=False, exists=True, resolve_path=True), multiple=True, help="Directory containing FASTA files to compare")
@click.option("-n", "--num-threads", "numThreads", type=int, default=None, help="Number of Threads to use (default 5 * number of cores)")
@click.option("-o", "--output", type=click.Path(dir_okay=False, exists=False), help="The location for the output CSV file")
@click.option("-s", "--save-compression", "saveCompression", type=click.Path(dir_okay=True, file_okay=False, resolve_path=True), default=None, help="Save compressed sequence files to the specified directory")
@click.option("-c", "--compression", default="lzma", type=click.Choice(['lzma', 'gzip', 'bzip2', 'zlib', 'lz4', 'snappy']), help="The compression algorithm to use")
@click.option("-p", "--show-progress", "showProgress", default=True, type=bool, help="Whether to show a progress bar for computing compression distances")
@click.option("-r", "--reverse_complement", is_flag=True, default=False, help="Whether to use the reverse complement of the sequence")
def cli(fasta, directories, numThreads, compression, showProgress, saveCompression, output, reverse_complement):

    # generate a list of absolute paths containing the files to be compared
    files = [Path(f) for f in fasta]

    for directory in directories:
        for dirpath, _, filenames in os.walk(directory):
            for f in filenames:
                f = Path(os.path.join(dirpath, f))
                if f.suffix.lower() in [".fasta", ".fna", ".fa", ".faa"]:
                    files.append()
    files = list(set(files)) # remove any duplicates
    sequences = []
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=numThreads)

    #compute compressed sizes of individual sequences
    print("Compressing individual files...")
    compressed_sizes = tqdm_parallel_map(executor, lambda x: compressed_size(filename=x,
                                                                             algorithm=compression,
                                                                             save_directory=saveCompression,
                                                                             ), files)
    compress_dict = dict(compressed_files) # {PATH: compressed size}

    # compute compressed sizes of all ordered pairs of sequences
    print("Compressing pairs...")
    compressed_pairs_sizes = tqdm_parallel_map(
        executor,
        lambda x: compressed_size(
            filename=x,
            algorithm=compression,
            save_directory=saveCompression
        ),
        itertools.permutations(compress_dict.keys())
    )
    compressed_pairs_dict = dict(compressed_pairs_sizes)

    distances = []
    for pair in compressed_dict.combinations():
        distances += {
            pair: compute_distance(
                compress_dict[pair[0]],
                compress_dict[pair[1]],
                compressed_pairs_dict[(pair[0], pair[1]])],
            compressed_pairs_dict[(pair[1], pair[0])]
        }
    print(distances)

    #
    #
    # df = pd.DataFrame(distances, columns=["file", "file2", "ncd"])#.to_csv("out.csv", index=False)
    #
    # df.pivot(index='file', columns='file2', values='ncd').to_csv(output)


def tqdm_parallel_map(executor, fn, *iterables, **kwargs):
    """
    Equivalent to executor.map(fn, *iterables),
        but displays a tqdm-based progress bar.
        Does not support timeout or chunksize as executor.submit is used internally
    **kwargs is passed to tqdm.
    """
    futures_list = []
    for iterable in iterables:
        futures_list += [executor.submit(fn, i) for i in iterable]
    if showProgress:
        print("Processes submitted, starting compression distance calculation...")
        for f in tqdm(concurrent.futures.as_completed(futures_list), total=len(futures_list), **kwargs):
            yield f.result()
    else:
        for f in concurrent.futures.as_completed(futures_list):
            yield f.result()

def compute_parallel(comparison, algorithm, saveCompression="", reverse_complement=False):
    #Compute a distance between a and b

    sizes = compressed_size(sequences, algorithm, saveCompression, comparison)
    ncd = compute_distance(sizes[0], sizes[1], sizes[2])
    return comparison[0], comparison[1], ncd


if __name__ == "__main__":
    cli()
