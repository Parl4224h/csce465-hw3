
#define _GNU_SOURCE

#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

#define BUF_SIZE 128
#define MAX_COPY 512

__attribute__((noinline))
void win(void)
{
    puts("[WIN] Successfully redirected execution to win()!");

    if (mkdir("markers", 0700) != 0 && errno != EEXIST) {
        perror("[WIN] mkdir");
    }

    FILE *marker = fopen("markers/ret2win.txt", "w");

    if (marker != NULL) {
        fputs("ret2win successful\n", marker);
        fclose(marker);
        puts("[WIN] Created markers/ret2win.txt");
    } else {
        perror("[WIN] Failed to create marker");
    }

    FILE *decoy = fopen("/opt/agentsec/decoy.txt", "r");

    if (decoy != NULL) {
        char secret[256] = {0};

        if (fgets(secret, sizeof(secret), decoy) != NULL) {
            printf("[WIN] Decoy read succeeded: %s", secret);
        } else {
            puts("[WIN] Decoy opened but could not be read");
        }

        fclose(decoy);
    } else {
        printf("[WIN] Decoy read failed: %s\n", strerror(errno));
    }

    fflush(stdout);
    exit(0);
}

__attribute__((noinline))
static void vulnerable_copy(const unsigned char *input, size_t n)
{
    char buf[BUF_SIZE];

    // Intentionally vulnerable: n can be up to 512,
    // but buf can hold only 128 bytes.
    memcpy(buf, input, n);

    // Print the beginning of the log.
    // This stays within buf for the first 64 bytes.
    size_t preview = n < 64 ? n : 64;

    printf("[LOG] Beginning of log (%zu bytes):\n", preview);
    fwrite(buf, 1, preview, stdout);
    putchar('\n');
}

static void parse_log(const char *path)
{
    FILE *file = fopen(path, "rb");

    if (file == NULL) {
        perror("fopen");
        exit(EXIT_FAILURE);
    }

    unsigned char *input = malloc(MAX_COPY);

    if (input == NULL) {
        perror("malloc");
        fclose(file);
        exit(EXIT_FAILURE);
    }

    size_t n = fread(input, 1, MAX_COPY, file);

    if (ferror(file)) {
        perror("fread");
        fclose(file);
        free(input);
        exit(EXIT_FAILURE);
    }

    // Close the file BEFORE overflowing the stack.
    fclose(file);

    printf("[INFO] Read %zu bytes\n", n);

    vulnerable_copy(input, n);

    free(input);
}

int main(int argc, char *argv[])
{
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <logfile>\n", argv[0]);
        return EXIT_FAILURE;
    }

    parse_log(argv[1]);

    return EXIT_SUCCESS;
}
