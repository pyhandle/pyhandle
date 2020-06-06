#ifndef HPY_UNIVERSAL_H
#define HPY_UNIVERSAL_H

#include <stdlib.h>
#include <stdint.h>
#include <stdarg.h>

#ifdef __GNUC__
#define _HPy_HIDDEN  __attribute__((visibility("hidden")))
#else
#define _HPy_HIDDEN
#endif /* __GNUC__ */

#define HPyAPI_RUNTIME_FUNC(restype) _HPy_HIDDEN restype

/* HPy types */
typedef intptr_t HPy_ssize_t;
struct _HPy_s { HPy_ssize_t _i; };
typedef struct _HPy_s HPy;
typedef struct _HPyContext_s *HPyContext;

/* compatibility CPython types */
#include "cpy_types.h"


/* misc stuff, which should probably go in its own header */
#define HPy_NULL ((HPy){0})
#define HPy_IsNull(x) ((x)._i == 0)

// XXX: we need to decide whether these are part of the official API or not,
// and maybe introduce a better naming convetion. For now, they are needed for
// ujson
static inline HPy HPy_FromVoidP(void *p) { return (HPy){(HPy_ssize_t)p}; }
static inline void* HPy_AsVoidP(HPy h) { return (void*)h._i; }

// include runtime functions
#include "common/macros.h"
#include "common/runtime/argparse.h"

#include "common/type.h"
#include "typeslots.h"
#include "meth.h"
#include "module.h"

#include "autogen_ctx.h"
#include "autogen_trampolines.h"

/* manual trampolines */

static inline HPy _HPy_New(HPyContext ctx, HPy h_type, void **data) {
    /* Performance hack: the autogenerated version of this trampoline would
       simply forward data to ctx_New.

       Suppose you call HPy_New this way:
           PointObject *point;
           HPy h = HPy_New(ctx, cls, &point);

       If you pass "data" to ctx->New, the C compiler must assume that anybody
       could write a different value at any time into this local variable
       because a pointer to it escaped. With this hack, it's no longer the
       case: what escaped is the address of data_result instead and that local
       variable disappears since this function is likely inlined.

       See https://github.com/pyhandle/hpy/pull/22#pullrequestreview-413365845
    */
    void *data_result;
    HPy h = ctx->ctx_New(ctx, h_type, &data_result);
    *data = data_result;
    return h;
}


#endif /* HPY_UNIVERSAL_H */
