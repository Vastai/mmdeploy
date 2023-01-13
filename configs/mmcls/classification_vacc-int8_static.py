_base_ = ['./classification_static.py', '../_base_/backends/vacc.py']

backend_config = dict(
    common_config=dict(
        name='mobilenetv2'
    ),
    model_inputs=[
        dict(
            shape=dict(input=[1, 3, 224, 224]),
            qconfig=dict(
                dtype='int8'
            )
        )
    ]
)
